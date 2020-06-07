vcl 4.0;

import directors;
import std;

backend default {
    .host = "haproxy";
    .port = "8080";
}

sub vcl_init {
    new vdir = directors.round_robin();
    vdir.add_backend(default);
}

sub vcl_recv {
    set req.backend_hint = vdir.backend();

    set req.http.grace = "none";

    
    if (req.http.Accept-Encoding) {
        if (req.http.Accept-Encoding ~ "gzip") {
            set req.http.Accept-Encoding = "gzip";
        } elsif (req.http.Accept-Encoding ~ "deflate") {
            set req.http.Accept-Encoding = "deflate";
        } else {
            unset req.http.Accept-Encoding;
        }
    }

    unset req.http.Cookie;

    if (req.url ~ "\.(jpg|png|gif|gz|tgz|bz2|tbz|mp3|ogg|swf|css|js)$") {
        return (hash);
    }

    return (hash);
}

sub vcl_hash {
    hash_data(req.url);

    if (req.http.host) {
        hash_data(req.http.host);
    } else {
        hash_data(server.ip);
    }

    return (lookup);
}

sub vcl_hit {
    if (obj.ttl >= 0s) {
        return (deliver);
    }

    if (std.healthy(req.backend_hint)) {
        if (obj.ttl + 10s > 0s) {
            set req.http.grace = "normal(limited)";
            return (deliver);
        } else {
            return (pass);
        }
    } else {
        if (obj.ttl + obj.grace > 0s) {
            set req.http.grace = "full";
            return (deliver);
        } else {
            return (pass);
        }
    }
}

sub vcl_miss {
    return (pass);
}

sub vcl_backend_response {
    set beresp.grace = 1d;

    unset beresp.http.Server;

    if (beresp.http.content-type ~ "(text|application)") {
        set beresp.do_gzip = true;
    }

    unset beresp.http.set-cookie;
    return (deliver);
}

sub vcl_deliver {
    unset resp.http.via;
    unset resp.http.x-varnish;
    set resp.http.grace = req.http.grace;

    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }

    return (deliver);
}