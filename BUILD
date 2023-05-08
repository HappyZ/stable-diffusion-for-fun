load("@rules_python//python:defs.bzl", "py_binary")
load("@subpar//:subpar.bzl", "par_binary")

package(default_visibility=["//visibility:public"])

par_binary(
    name="frontend",
    srcs=["frontend.py"],
    deps=[
        "//utilities:constants",
        "//utilities:database",
        "//utilities:logger",

        "//utilities:times",
    ],
    data=[
        "templates/index.html",
    ],
)

par_binary(
    name="backend",
    srcs=["backend.py"],
    deps=[
        "//utilities:constants",
        "//utilities:database",
        "//utilities:logger",
        "//utilities:model",
        "//utilities:text2img",
        "//utilities:translator",
        "//utilities:img2img",
        "//utilities:times",
    ],
)
