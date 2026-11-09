# Producer contract fixtures

The `upstream` directory contains the Management Agent's executable fixture corpus from
[producer issue #324](https://github.com/tinkerologie/unraid-management-agent/issues/324).
`pin.json` records the exact revision and a checksum for each upstream file.
CI reads the committed files and does not fetch fixtures or contact Unraid.

To update the corpus, choose a full producer commit and copy its `contracts/v1`
files verbatim. Update the pin, checksums, and consumer assertions together.
Review changes to values and event ownership as well as to the JSON shape.

The `legacy` directory contains synthetic examples of formats this integration
still supports. It covers the old syslog key and counts, share counters without
`storage_*`, UPS runtime alias, ZFS corruption count, and older event envelopes
or payloads. The legacy examples are compatibility tests with separate provenance.
