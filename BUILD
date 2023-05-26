load("@rules_python//python:defs.bzl", "py_binary")
load("@subpar//:subpar.bzl", "par_binary")

package(default_visibility=["//visibility:public"])

# subpar broke flask file path, don't buidl with .par
par_binary(
    name="frontend",
    srcs=["frontend.py"],
    deps=[
        "//utilities:constants",
        "//utilities:database",
        "//utilities:logger",
    ],
    data=[
        "templates/index.html",
        "static/bootstrap.min.css",
        "static/jquery-3.6.1.min.js",
        "static/bootstrap.bundle.min.js",
        "static/jquery.sketchable.min.js",
        "static/jsketch.min.js",
        "static/jquery.sketchable.memento.min.js",
        "static/masonry.pkgd.min.js",
        "static/imagesloaded.pkgd.min.js",
    ],
)

par_binary(
    name="backend",
    srcs=["backend.py"],
    deps=[
        "//utilities:constants",
        "//utilities:database",
        "//utilities:memory",
        "//utilities:logger",
        "//utilities:model",
        "//utilities:config",
        "//utilities:text2img",
        "//utilities:translator",
        "//utilities:img2img",
        "//utilities:inpainting",
        "//utilities:times",
    ],
)
