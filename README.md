# WAD - Web application detector
[![Build Status](https://travis-ci.org/CERN-CERT/WAD.svg?branch=master)](https://travis-ci.org/CERN-CERT/WAD)

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
