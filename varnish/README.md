# What is Varnish

Varnish is a caching HTTP reverse proxy. It is installed in front of any server that speaks HTTP (nginx for example), so any HTTP request that would go to that server is first sent to Varnish, and after Varnish handles the request as configured it's send back to the HTTP server.

Varnish caches data based on how it's configured. The most common way is to cache all the static data (images, JS scripts etc.). Varnish stored all this cached data in a virtual memory and when it receives a request it tries to answer the request from this cache. If it can't answer the request from the cache it will forward the request to the HTTP server, fetch the response and then store it in the cache for future use.

[Varnish overview video](https://www.youtube.com/watch?v=fGD14ChpcL4)

## Varnish Configuration Language (VCL)

The primary configuration method for Varnish is Varnish Configuration Language, or VCL for short. It's a domain specific language which Varnish translates to binary code and then executes as requests arrive. VCL has much common in C with it's syntax and it shouldn't be too hard to write and understand.

The methods or states in Varnish are called subroutines and Varnish includes some built-in subroutines that start with ```vcl_``` prefix. These subroutines can have actions with which they pass data to other subroutines. An example of a built-in subroutine is ```vcl_recv``` which is called at the beginning of a request.

To read more from VCL and get familiar with it's syntax and submodules read [VCL tutorial](https://www.varnish-software.com/wiki/content/tutorials/varnish/vcl.html) and [VCL documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl.html).

### Further reading

* [Introduction to Varnish](https://varnish-cache.org/intro/index.html#intro)
* [Varnish documentation](https://varnish-cache.org/docs/trunk/)
* [Varnish Users Guide](https://varnish-cache.org/docs/trunk/users-guide/index.html#users-guide-index)  
* [Varnish in Wikipedia](https://en.wikipedia.org/wiki/Varnish_(software))