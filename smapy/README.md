ABI API
=======

This document describes the available API resources and the parameters that they expect.


**ProcessSite**
------------

The **ProcessSite** resource run all the stage resources on a single site:

* Crawling: crawling.CrawlSite
* Parsing: parsing.ParseUrls
* Mapping: map.Posts
* Analysis: analuze.Post

Everything is run in a single process but taking advantage of gevent concurrency.
This is because this resource will be called in multiple processes at the same time,
having each one of them work on a different site.
For this reason, in order to call it individually, some extra parameters are needed.

### Details

* **resource:** `main.ProcessSite`
* **endpoint:** `/process\_site`
* **methods":** `POST`

### Parameters

* **site_url**: Site `_id` in the `sites` collection.
* **site_type**: Type of Mapper to use during the mapping phase.
* **urls**: Number of URLs to crawl.
* _concurrency_: Maximimum number of concurrent greenlets to spawn. This value must be kept within
sensible ranges, otherwise the http sessions get full and some connections can be dropped.
If not provided, it gets its value from the configuration.

### Results

An action summary is provided in the results field containing:

* _crawl\_results_: The number of URLs by crawling status.
* _parsed_: the number of posts that have been found by the parser.
* _posts_: the number of posts that have been successfullt imported.
* _duplicated\_posts_: the number of posts that were duplicates.
* _occurrences_: the number of occurrences found during the analysis.

### Example

```
POST http://localhost:8001/process_site
{
    "site_url": "http://foodbabe.com",
    "site_type": "blog",
    "urls": 3
}

{
    "status": "200 OK",
    "out_ts": "2016-11-28T13:15:09.870894",
    "host": "a.host",
    "elapsed": 31168.852,
    "in_ts": "2016-11-28T13:14:38.702042",
    "results": {
        "crawl_results": {
            "scraped": 3,
            "redirect": 0
        },
        "duplicated_posts": 3,
        "parsed": 6,
        "posts": 3,
        "occurrences": 121
    },
    "pid": 29806,
    "session": "583c2dbede916d746e261f8d"
}
```


**CrawlSite**
-------------

The **CrawlSite** resource crawls multiple URLs from a single site.

### Details

* **resource:** `crawling.CrawlSite`
* **endpoint:** `/crawl_site`
* **methods":** `POST`

### Parameters

* **urls**: Number of URLs to crawl from the site.
* **site_url**: Root URL from the site. It has to match the `_id` of the `sites` collection.
* **site_type**: Type of Mapper to use during the mapping phase.
* _concurrency_: Maximimum number of concurrent greenlets to spawn during the crawler. If not given, it is taken from the config.

### Results

An action summary is provided in the results field containing the list of URLs crawled grouped by their status.

### Example

```
GET http://localhost:8001/crawl_site
{
    "site_url": "http://www.crazyforcrust.com/",
    "site_type": "blog",
    "urls": 3
}

{
    "results": {
        "redirect": [],
        "scraped": [
            "http://www.crazyforcrust.com/",
            "http://www.crazyforcrust.com/poultry/",
            "http://www.crazyforcrust.com/2016/11/cookies-n-cream-oreo-cake-roll/"
        ]
    },
    "host": "a.host",
    "status": "200 OK",
    "in_ts": "2016-11-29T09:48:59.225327",
    "elapsed": 1675.387,
    "session": "583d4f0bde916d13240fe54f",
    "out_ts": "2016-11-29T09:49:00.900714",
    "pid": 4900
}
```


**CrawlSites**
-------------

The **CrawlSites** resource gets a list of sites from DB and launches the **CrawlSite** resource in multiple processes

### Details

* **resource:** `crawling.CrawlSites`
* **endpoint:** `/crawl`
* **methods":** `GET`, `POST`

### Parameters

* **urls**: Number of URLs to crawl from each site.
* _limit_: Maximum number of sites to crawl. If not given, it crawls all the sites that can be found in DB.
* _concurrency_: Maximimum number of concurrent greenlets to spawn for each site. If not given, it is taken from the config.

**NOTE**: The `site_type` and `site_url` are taken from DB, so they are not needed in this case.

### Results

An action summary is provided in the results field containing the list of URLs crawled grouped by their status.

### Example

```
GET http://localhost:8001/crawl?limit=2&processes=1&urls=3

{
    "status": "200 OK",
    "out_ts": "2016-11-28T13:34:06.671924",
    "host": "a.host",
    "elapsed": 9909.416,
    "in_ts": "2016-11-28T13:33:56.762508",
    "results": {
        "scraped": [
            "http://forum.bjcp.org",
            "http://forum.bjcp.org/memberlist.php?mode=group&g=2197&sid=5ce1cba7efd3584e716bc33733178d00",
            "http://forum.bjcp.org/viewonline.php?sid=5ce1cba7efd3584e716bc33733178d00",
            "http://www.city-data.com/forum/vegetarian-vegan-food/",
            "http://www.city-data.com/forum/vegetarian-vegan-food/index11.html",
            "http://www.city-data.com/forum/vegetarian-vegan-food/2654838-part-time-vegetarians-2.html"
        ],
        "redirect": []
    },
    "pid": 31593,
    "session": "583c3244de916d7b697cd2c2"
}
```


**ParseUrls**
-------------

The **ParseUrls** resource parses a given list of URLs.

### Details

* **resource:** `parsing.ParseUrls`
* **endpoint:** `/parse`
* **methods":** `POST`

### Parameters

* _urls_: List of URLs to parse. They need to have been crawled before, so that their HTMLs are stored in GridFS. Required if `url_clusters` is not given.
* _url_clusters_: Dictionary containing lists of URLs grouped by cluster. If this is not provided, `urls` will be used to create the clusters.

### Results

The details of what has been done is included in the results fields including:

* _urls_: The list of URLs that have been processed.
* _parsed_: The list of URLs that have been succesfully parsed.
* _posts_: The list of posts that have been found while parsing the URL HTMLs.
* _clusters_: The list of cluster ids.

**WARNING**: This is intended for internal usage, so the response can be **huge**.

### Example

No example is provided for the reason stated right above.


**ParseCrawled**
-------------

The **ParseCrawled** resource gets the list of crawled (but still unparsed) URLs from DB and invokes the **ParseUrls** resource.

**TODO**: This resource is currently running everything within a single process. This should be changed, grouping the URLs by site
and passing each one of them to a different process.

### Details

* **resource:** `parsing.ParseCrawled`
* **endpoint:** `/parse_crawled`
* **methods":** `GET`, `POST`

### Parameters

* _match_: A MongoDB query can be given to filter the URLs that will be parsed.

### Results

An action summary is provided in the results field containing:

* _urls_: The number of URLs that were found in DB.
* _parsed_: The number of URLs that have been succesfully parsed.
* _posts_: The number of posts that have been found while parsing the URL HTMLs.
* _clusters_: The number of clusters that the URLs were grouped in.

### Example

```
GET http://localhost:8001/parse_crawled

{
    "results": {
        "urls": 3,
        "parsed": 3,
        "posts": 9,
        "clusters": 1
    },
    "host": "a.host",
    "status": "200 OK",
    "in_ts": "2016-11-29T10:12:06.490771",
    "elapsed": 312.213,
    "session": "583d5476de916d13240fe559",
    "out_ts": "2016-11-29T10:12:06.802984",
    "pid": 4900
}
```


**MapParsed**
-------------

The **MapParsed** resource gets the list of parsed data and maps them into real posts.

### Details

* **resource:** `mapping.MapParsed`
* **endpoint:** `/map`
* **methods":** `GET`, `POST`

### Parameters

* _source_: Optionally indicate a different collection to get the parsed data from. This defaults to `parsed` and normally should not be changed.
* _source_data_: Optionally provide a list of dictionaries to map. This should only be used internally or for debugging purposes.
* _limit_: Limit the number of posts to get from DB.
* _match_: MongoDB query to filter which posts to get from DB.
* _site_type_: Override the site_type. This should be used only for debugging purposes.

### Results

An action summary is provided in the results field containing:

* _posts_: The number of posts successfully mapped.
* _duplicated_posts_: The number of that have been discarded because they already existed in DB.

### Example

```
GET http://localhost:8001/map

{
    "results": {
        "duplicated_posts": 68,
        "posts": 687
    },
    "host": "a.host",
    "status": "200 OK",
    "in_ts": "2016-11-29T10:40:15.302406",
    "elapsed": 1686.626,
    "session": "583d5b0fde916d13240fe563",
    "out_ts": "2016-11-29T10:40:16.989032",
    "pid": 4900
}
```


**AnalyzePosts**
-------------

The **AnalyzePosts** resource gets the mapped but still unanalyzed posts afrom DB and analyzes them.

### Details

* **resource:** `analysis.AnalyzePosts`
* **endpoint:** `/analyze`
* **methods":** `GET`, `POST`

### Parameters

* _reanalyze_: Optional boolean flag indicating whether old posts should be reanalyzed or not. It defaults to False.
* _concurrency_: Maximimum number of concurrent greenlets to spawn. If not given, it is taken from the config.
* _posts_: Optionally provide the posts to analyze. This is intended to be used only internally or for debugging purposes.
* _match_: Optional MongoDB query to filter which posts to get from DB and analyze.

### Results

An action summary is provided in the results field containing:

* _posts_: The number of posts that have been analyzed.
* _occurrence_posts_: The number of posts that had occurrences.
* _occurrences_: The number of occurrences found.
* _relevant_coccurrences_: The number of occurrences considered relevant.

### Example

```
GET http://localhost:8001/analyze

{
    "results": {
        "occurrences": 3763,
        "occurrence_posts": 368,
        "posts": 687,
        "relevant_occurrences": 3756
    },
    "host": "xals.cat",
    "status": "200 OK",
    "in_ts": "2016-11-29T12:17:45.026731",
    "elapsed": 227554.469,
    "session": "583d71e9de916d3d0528ef6a",
    "out_ts": "2016-11-29T12:21:32.581200",
    "pid": 15621
}
```