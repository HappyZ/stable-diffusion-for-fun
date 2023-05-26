load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility=["//visibility:public"])

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
    name="database",
    srcs=["database.py"],
    deps=[
        ":logger",
        ":times",
        ":images",
        ":constants",
    ],
)

py_library(
    name="envvar",
    srcs=["envvar.py"],
)

py_test(
    name="envvar_test",
    srcs=["envvar_test.py"],
    deps=[":envvar"],
)

py_library(
    name="images",
    srcs=["images.py"],
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

py_library(
    name="memory",
    srcs=["memory.py"],
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
    name="text2img",
    srcs=["text2img.py"],
    deps=[
        ":constants",
        ":config",
        ":logger",
        ":images",
        ":memory",
        ":model",
        ":times",
    ],
)

py_library(
    name="img2img",
    srcs=["img2img.py"],
    deps=[
        ":constants",
        ":config",
        ":logger",
        ":images",
        ":memory",
        ":model",
        ":times",
    ],
)

py_library(
    name="inpainting",
    srcs=["inpainting.py"],
    deps=[
        ":constants",
        ":config",
        ":logger",
        ":images",
        ":memory",
        ":model",
        ":times",
    ],
)

py_library(
    name="times",
    srcs=["times.py"],
)

py_test(
    name="times_test",
    srcs=["times_test.py"],
    deps=[":times"],
)

py_library(
    name="translator",
    srcs=["translator.py"],
)
