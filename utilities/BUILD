load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "memory",
    srcs = ["memory.py"],
)

py_library(
  name = "logger",
  srcs = ["logger.py"],
)

py_test(
  name = "logger_test",
  srcs = ["logger_test.py"],
  deps = [":logger"],
)
