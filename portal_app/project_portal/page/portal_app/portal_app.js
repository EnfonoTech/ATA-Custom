frappe.pages["portal_app"].on_page_load = function (wrapper) {
    // The bundle is content-hashed per build, so ask the server for today's names.
    frappe.call("portal_app.api.public.get_frontend_bundle").then(function (r) {
        var bundle = (r && r.message) || { js: [], css: [] };
        var pending = bundle.css.length;
        var start = function () {
            wrapper.innerHTML = `<div id="app"></div>`;
            var _$ = window.$;
            var _jQuery = window.jQuery;
            bundle.js.forEach(function (src) {
                var script = document.createElement("script");
                script.type = "module";
                script.src = src;
                script.onload = function () {
                    window.$ = _$;
                    window.jQuery = _jQuery;
                };
                document.body.appendChild(script);
            });
        };
        if (!pending) return start();
        bundle.css.forEach(function (href) {
            var link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = href;
            link.onload = link.onerror = function () {
                pending -= 1;
                if (pending === 0) start();
            };
            document.head.appendChild(link);
        });
    });
};
