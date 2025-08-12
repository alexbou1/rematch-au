## rematch-au

<p align="left">
  <img style="width: 40%" src="assets/rematch.svg" />
</p>

> [!NOTE]  
> This repo is still a work in progress and should be treated like a proof of concept.

Australian address matching tool that compares input addresses to the
[GNAF public dataset](https://data.gov.au/data/dataset/geocoded-national-address-file-g-naf).
### Get started

#### Setup:
```shell
python3 -m venv venv
. venv/bin/activate
python3 -m pip install .
rematch-au init-db  # ~5-10 mins
```

To run a particular address
```shell
rematch-au match -a '245 HIGH STREET PRAHRAN VIC 3181' -s 'PRAHRAN' -j 'VIC' -p '3181'
```

### Credits
Special thanks to Murray for his guidance and inspiration on packaging, and for
providing key tools that made testing and development so much smoother.

Also to [DuckDB](https://duckdb.org/) for the awesome work they are doing.
