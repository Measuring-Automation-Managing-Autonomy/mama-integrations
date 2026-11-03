# Maintainers — mama-integrations

**Status:** draft

| Role | Holder | Responsibility |
|---|---|---|
| Repository maintainer | [@emmanuel-a-otchere](https://github.com/emmanuel-a-otchere) | Adapter code, version gates, releases |
| Framework & Interoperability Group liaison | *vacant* | Interface contract alignment with `mama-framework` and upstream `mama` maintainers |
| Upstream coordination contact | [@emmanuel-a-otchere](https://github.com/emmanuel-a-otchere) (also upstream `mama` maintainer) | Ruleset/schema change awareness |

## Rules this maintainer upholds

- No scoring logic ever enters this repository — PRs adding level/weakest-link/dimension logic are rejected on sight (ADR + integration-contract rule 2).
- Upstream MAJOR version support is added only after the upstream maintainers publish migration guidance, and only with an ADR + compatibility-matrix update.
- Releases declare the supported upstream versions table in `compatibility.md`; the table and `versions.py` must agree (CI-checked).

Conflicts of interest: the current maintainer is also the upstream `mama` maintainer — recorded here per the governance separation rules; framework-level decisions about the interface still go through the Stewardship Council process. Succession and appeals: org [GOVERNANCE.md](https://github.com/Measuring-Automation-Managing-Autonomy/.github/blob/main/GOVERNANCE.md).
