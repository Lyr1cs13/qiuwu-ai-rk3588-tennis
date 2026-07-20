# Contributing

Contributions are welcome for the published edge reference: UI improvements, V4L2
device compatibility, result-contract tooling, generic cloud adapters,
documentation, tests, and deployment ergonomics.

Before opening a pull request, run:

```bash
python3 qiuwu.py demo --mode match --validate-only
python3 qiuwu.py demo --mode side --validate-only
```

Do not submit trained weights, source videos, annotations, cloud credentials,
private runtime code, camera firmware, device-tree patches, or unpublished
production parameters. Please keep contributions compatible with the public
component contracts in `edge_runtime/` and `contracts/`.
