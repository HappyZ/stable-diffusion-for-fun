load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility=["//visibility:public"])

py_library(
    name="memory",
    srcs=["memory.py"],
)

py_library(
    name="text2img",
    srcs=["text2img.py"],
    deps=[
        ":config",
        ":model",
    ],
)

py_library(
    name="config",
    srcs=["config.py"],
    deps=[
        ":logger",
        ":constants",
    ],
)

py_library(
    name="constants",
    srcs=["constants.py"],
)

py_library(
    name="model",
    srcs=["model.py"],
    deps=[
        ":constants",
        ":memory",
        ":logger",
    ],
)

py_library(
    name="logger",
    srcs=["logger.py"],
)

py_test(
    name="logger_test",
    srcs=["logger_test.py"],
    deps=[":logger"],
)
