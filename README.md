# ezsp-counters
Proof of concept EZSP counters custom component for Home Assistant. Work only with EZSP based radios

## Requirments
 - custom [`bellows`](https://github.com/Adminiuga/bellows/tree/ac/ezsp-counters) fork

During the configuration, two options are available:

- "_Counter Entities_" -- Register sensor entities for each EZSP counter
- "_HTTP Endpoint_" -- Register and http endpoint to return a list of EZSP counters

If sensor entities are created, you may want to filter those from `recorder` and `history`
components. This option is no longer recommended.

The recommended option is to use the _http endpoint_and [telegraf](https://docs.influxdata.com/telegraf/)
The http endpoint is registered under `/api/ezsp_counters/guid` where guid is unique for each
configuration. Exact URL is logged during Home Assistant start.

Sample `telegraf.conf` input plugin configuration

```
[[inputs.http]]
  ## One or more URLs from which to read formatted metrics
  urls = [
    "https://ha.local:8123/api/ezsp_counters/11111111-2222-3333-4444-5555555"
  ]

  ## HTTP method
  method = "GET"

  ## Optional TLS Config
  tls_ca = "/etc/letsencrypt/live/ha.local/chain.pem"

  data_format = "json"
  tag_keys = [
        "counter"
  ]
  json_name_key = "collection"
```
