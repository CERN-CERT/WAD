# WAD - Web application detector
[![Build Status](https://travis-ci.org/CERN-CERT/WAD.svg?branch=master)](https://travis-ci.org/CERN-CERT/WAD) [![PyPI](https://img.shields.io/pypi/v/wad.svg)](https://pypi.python.org/pypi/wad)

WAD lets you analyze given URL(s) and detect technologies used by web application behind that URL, 
from the OS and web server level, to the programming platform and frameworks, as well as server- and client-side
applications, tools and libraries. 

For example, results of scan of server might include: 

  * OS: Windows, Linux...
  * Web server: Apache, Nginx, IIS...
  * Programming platform: PHP, Python, Ruby, Java...
  * Content management systems: Drupal, WordPress...
  * Frameworks: AngularJS, Ruby on Rails, Django...
  * various databases, analytics tools, javascript libaries, CDNs, comment systems, search engines and many others.
  

## How it works
WAD is built as a standalone application, using [Wappalyzer](https://github.com/AliasIO/Wappalyzer)'s
detection rules. It sends a GET request to the given URL and analyzes both HTTP response header and body (HTML page), 
looking for indications to discover web technologies used. 

Detection results may include information about versions of technologies used, for example Linux distro or Apache version. 
Results are categorized depending on type of technology (whether it is CMS or database etc.). There are now over 700 
technologies that can be discovered using WAD.

## Installation
[WAD is available via PyPI](https://pypi.python.org/pypi/wad), so in order to install it, you simply need to run following command:

`pip install wad`

## Usage
Use `wad -h` to print help text.
JSON is used for convenient formatting of output data.
### Example usage scenario
Command: `wad -u https://pypi.python.org/` 

Output:

```
{
    "https://pypi.python.org/pypi": [
        {
            "type": "cache-tools", 
            "app": "Varnish", 
            "ver": null
        }, 
        {
            "type": "web-servers", 
            "app": "Nginx", 
            "ver": "1.6.2"
        }
    ]
}
```

## Differences between WAD and Wappalyzer
Although most of the rules matching functionality is simply a Python port of Wappalyzer's javascript implementation, there are some key differences between projects.

First of all, Wappalyzer (as an extension) runs on top of web browser, which means that the scripts on scanned site were ran, so variables and objects are created and accessible. 
Unfortunately, this isn't and won't be a case for WAD. WAD parses raw site content (as delivered by HTTP response), without running it in browser context. 
The consequences of that are simple - we can't use Wappalyzer's rules, that search for variables and objects in Javascript environment.

Secondly, the project has and will continue to naturally diverge from Wappalyzer's codebase. We don't aim to make one-to-one port of Wappalyzer project and with intention to move to BeautifulSoup as DOM inspector (instead of blindly parsing the website with regex), we won't be able to assure same behaviour in every case. 

Finally, additional features added into WAD project aren't ported into Wappalyzer at the same time.

## Changelog
### 0.2.0 (2015-08-10)

**Implemented enhancements:**

- Multiple output formats (added Human readable text, CSV)
- Some methods extracted from Detector's detect method.
- Minor bugfixes
