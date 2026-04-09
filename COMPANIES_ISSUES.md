# Company Issues Protocol

Last verified: 2026-04-09

## All Active Companies (97): PASSED

All 97 companies with `status: active` in `companies_catalog.yaml` were tested
against their ATS API endpoints. All returned HTTP 200 with valid JSON.

3 companies returned 0 postings (board exists but empty):
- Retool (ashby/retool)
- Owkin (greenhouse/owkin)
- World Labs (ashby/worldlabs)

## Companies with No Supported ATS (status: no_adapter)

These companies use ATS systems we don't have adapters for. They cannot be
auto-tracked and need to be checked manually via their careers pages.

| Company | ATS Used | Careers URL | Reason |
|---|---|---|---|
| Hugging Face | Workable | apply.workable.com/huggingface/ | No Workable adapter |
| AI21 Labs | Comeet | www.comeet.com/jobs/ai21/E6.001 | No Comeet adapter |
| Quantexa | Workable | apply.workable.com/quantexa/ | No Workable adapter |

## Companies Removed (acquired or shut down, as of April 2025)

| Company | Reason | Parent Company |
|---|---|---|
| Codeium / Windsurf | Acquired by Cognition (Apr 2025) | Cognition (tracked) |
| Replicate | Acquired by Cloudflare (2025) | Cloudflare (tracked) |
| Weights & Biases | Acquired by CoreWeave (May 2025) | CoreWeave |
| Humanloop | Acqui-hired by Anthropic (Aug 2025) | Anthropic (tracked) |
| Orby AI | Acquired by Uniphore (Aug 2025) | Uniphore (Workday, no adapter) |

## Companies with Deactivated Boards

These companies previously had supported ATS boards that are now gone.
No workaround found.

| Company | Old ATS/Slug | Status | Notes |
|---|---|---|---|
| Luma AI | ashby/lumalabs | Board deactivated | Tried luma, luma-ai, lumaai -- all 404 |
| Sakana AI | ashby/sakanaai | No public ATS | Uses Google Form (careers@sakana.ai) |
| Patronus AI | ashby/patronusai | Moved to Rippling | ats.rippling.com/patronus-ai-jobs (no adapter) |
| Galileo | ashby/rungalileo | Moved to Rippling | ats.rippling.com/galileo (no adapter) |
| Helicone | ashby/helicone | No public ATS | Uses Notion job board |
| Genspark | ashby/genspark | Moved to Gem | jobs.gem.com/genspark (no adapter) |
| Freepik | greenhouse/freepik | Moved to Factorial HR | freepik-company.factorialhr.com (no adapter) |
| Sprinklr | greenhouse/sprinklr | Moved to Workday | Workday adapter tried, no responsive subdomain |
| 11x | ashby/11x | API disabled | Board page exists but posting API returns 404 |
| All Hands AI | ashby/allhandsai | Moved to JazzHR | allhandsai.applytojob.com (no adapter) |
| Crescendo | jazzhr/crescendoai | JazzHR | No adapter |
| Maven AGI | workable/mavenagi | Workable | No adapter |
