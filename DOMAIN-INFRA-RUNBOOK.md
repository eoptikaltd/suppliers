# Atlas — custom domain + shared load balancer runbook

One-time infra so every Atlas tool gets a stable `*.eoptika.com` URL behind one
shared Google Cloud external HTTPS load balancer, instead of default
`*.run.app` URLs. This does **not** change auth: each tool keeps its own
native Cloud Run IAP (the `--iap` flag + `iap.httpsResourceAccessor` binding
already in `CLAUDE.md`'s per-tool deploy step). The load balancer only does
TLS termination + host-based routing to the right Cloud Run service.

Nothing in this file has been executed. Run nothing here without an explicit
go-ahead — it touches shared DNS, a shared cert, and (for the tools already
live) production traffic.

## Open items to confirm before running anything

1. **DNS host for eoptika.com** (Cloudflare / GoDaddy / Google Domains /
   other) — needed to create the A records in step 6. I don't have registrar
   access; this half is yours.
2. **Confirm eoptika.com is clear to use** for these subdomains — not already
   serving the storefront or something else on the same labels.
3. **Service-name mapping is NOT what nav.json implies.** `nav.json` marks
   several tools `"status": "live"`, but none of the 19 tool-ids
   (`datawarehouse`, `moneyprint`, `suppliers`, …) match an actual deployed
   Cloud Run service name. What's actually running in `europe-west1` today:

   | Cloud Run service (real) | Likely nav.json tool-id | Confidence |
   |---|---|---|
   | `eoptika-data-warehouse` | `datawarehouse` — **but this is a different, older deployment than the tool we just built locally (which hasn't been deployed anywhere yet)** | needs your confirmation — replace it, or does it serve something else? |
   | `parcel-control-room` | `wimo` (CLAUDE.md's own control_room example is "Parcel Control Room") | likely |
   | `seo-atlas` | `pseo` | likely |
   | `blue-berry-sourcing-monitor` | `suppliers` (list_monitor example tool is "Blue-Berry Sourcing Monitor") | likely |
   | `mrsonder-sourcing-monitor` | none obviously — possibly a separate, not-yet-in-nav tool | unconfirmed |
   | `erp-connector-adhoc`, `general-tracking-webhook`, `llm-gateway`, `eoptika-vibe-coding` | none — these are backend/connector services, not Atlas UI tools | n/a, exclude from the LB |

   `moneyprint`, `cockpit`, `enrichment`, `devops` show no matching service at
   all despite `moneyprint`/`enrichment`/`devops` being marked `"live"` in
   `nav.json` — so that status field is aspirational, not ground truth. **Only
   wire a NEG/backend-service for a tool once you've confirmed which real
   service (if any) backs it.** Everything marked `build`/`plan` in
   `nav.json` has no service yet by definition — add those incrementally as
   each one deploys, not now.

4. **Final subdomain spelling** — table below is derived by taking
   `nav.json`'s current URLs and swapping `*.atlas.eoptika.hu` →
   `*.eoptika.com`. Flag any renames when you prepare the subdomains
   (your message mentioned "parcels" — nothing in `nav.json` is literally
   named that; closest match is `wimo` → `wimo.eoptika.com`, or `boomerang` →
   `returns.eoptika.com`. Confirm which you mean.)

## Subdomain list (19 total, from nav.json)

| Tool id | New URL | nav.json status |
|---|---|---|
| atlas (home) | atlas.eoptika.com | live (no backing service seen) |
| moneyprint | moneyprint.eoptika.com | live (no backing service seen) |
| cockpit | cockpit.eoptika.com | build |
| datawarehouse | datawarehouse.eoptika.com | live — see mapping note above |
| enrichment | enrichment.eoptika.com | live (no backing service seen) |
| devops | devops.eoptika.com | live (no backing service seen) |
| pseo | seo.eoptika.com | live — likely `seo-atlas` |
| radar | radar.eoptika.com | build |
| marketplaces | marketplaces.eoptika.com | plan |
| iris | iris.eoptika.com | build |
| suppliers | suppliers.eoptika.com | live — likely `blue-berry-sourcing-monitor` |
| wimo | wimo.eoptika.com | build — likely `parcel-control-room` |
| warehouse | warehouse.eoptika.com | plan |
| lab | lab.eoptika.com | plan |
| boomerang | returns.eoptika.com | plan |
| cs | cs.eoptika.com | plan |
| finance | finance.eoptika.com | plan |
| legal | legal.eoptika.com | plan |
| hr | hr.eoptika.com | plan |

## Architecture

19x DNS A record → 1 static IP → 1 target HTTPS proxy → 1 Google-managed cert
(19 SANs) → 1 URL map (host-based rules) → 1 backend service per *live* tool
→ 1 serverless NEG per *live* tool → existing Cloud Run service (IAP
unchanged). Tools still `build`/`plan` get their NEG/backend-service/host
rule added when they actually deploy — don't pre-create them.

## GCP-side steps (I can run these once the mapping + domain are confirmed)

**1. Reserve a static IP**
```
gcloud compute addresses create atlas-lb-ip --global \
  --project natural-caster-496309-j3
gcloud compute addresses describe atlas-lb-ip --global \
  --project natural-caster-496309-j3 --format="value(address)"
```

**2. Google-managed SSL cert — only include hostnames whose DNS (step 6) will
exist, or it stays stuck PROVISIONING forever.** Start with the confirmed-live
ones and add the rest in a later cert (certs aren't editable in place — adding
a host later means creating a new cert resource and swapping it onto the
proxy).
```
gcloud compute ssl-certificates create atlas-cert \
  --domains=datawarehouse.eoptika.com,seo.eoptika.com,suppliers.eoptika.com,wimo.eoptika.com \
  --global --project natural-caster-496309-j3
```

**3. Per tool: one serverless NEG + one backend service** (example for
datawarehouse — repeat once its real Cloud Run service name is confirmed;
placeholder `SERVICE_NAME` below)
```
gcloud compute network-endpoint-groups create neg-datawarehouse \
  --region=europe-west1 --network-endpoint-type=serverless \
  --cloud-run-service=SERVICE_NAME --project natural-caster-496309-j3

gcloud compute backend-services create bs-datawarehouse \
  --global --load-balancing-scheme=EXTERNAL_MANAGED \
  --project natural-caster-496309-j3

gcloud compute backend-services add-backend bs-datawarehouse \
  --global --network-endpoint-group=neg-datawarehouse \
  --network-endpoint-group-region=europe-west1 \
  --project natural-caster-496309-j3
```

**4. URL map — one map, one host rule per live tool**
```
gcloud compute url-maps create atlas-url-map \
  --default-service=bs-atlas --project natural-caster-496309-j3

gcloud compute url-maps add-path-matcher atlas-url-map \
  --path-matcher-name=datawarehouse-matcher \
  --default-service=bs-datawarehouse \
  --new-hosts=datawarehouse.eoptika.com \
  --project natural-caster-496309-j3
```
(repeat `--path-matcher-name`/`--new-hosts`/`--default-service` per tool)

**5. Target HTTPS proxy + global forwarding rule**
```
gcloud compute target-https-proxies create atlas-https-proxy \
  --url-map=atlas-url-map --ssl-certificates=atlas-cert \
  --project natural-caster-496309-j3

gcloud compute forwarding-rules create atlas-https-rule \
  --global --target-https-proxy=atlas-https-proxy \
  --address=atlas-lb-ip --ports=443 --project natural-caster-496309-j3
```

## DNS-side steps (yours — registrar for eoptika.com)

**6. One A record per live-tool hostname**, pointing at the static IP from
step 1. Do this before/alongside step 2 — the managed cert won't leave
PROVISIONING until every one of its SANs resolves to that IP. Propagation +
Google's validation can take anywhere from minutes to ~24h.

## After it's live

**7. Update `nav.json`** — swap every URL from `*.atlas.eoptika.hu` to the
confirmed `*.eoptika.com` scheme. I'll make this edit once the domain and
mapping above are confirmed.

**8. Move `nav.json` to the shared assets bucket** (alongside the CSS/fonts/
sprite already planned for `assets.atlas.eoptika.hu`) and have each tool's
`app.py` fetch it remotely with a short cache instead of bundling a local
copy. This is what turns "add a tool to the menu" into a one-file bucket
edit instead of a redeploy of all 19 tools — a small, one-time code change
(~10 lines) to the dev kit, independent of the domain work above. Happy to
make this change now if you want it done ahead of the domain confirmation.

**9. Verify** — once cert status is `ACTIVE`
(`gcloud compute ssl-certificates describe atlas-cert`), browse (not curl —
IAP needs a full OAuth redirect) to each hostname and confirm it reaches the
Google sign-in gate for `atlas-staff@eoptika.com`, then lands on the right
tool with the sidebar populated from the shared nav.

## Cost

One shared external HTTPS LB (~$18/mo base + minor per-GB) covers all 19
tools — far cheaper than a load balancer per tool. Cloud Run itself stays
pay-per-use.
