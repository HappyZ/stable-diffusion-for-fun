load("@rules_python//python:defs.bzl", "py_binary")
load("@subpar//:subpar.bzl", "par_binary")

package(default_visibility = ["//visibility:public"])

par_binary(
  name = 'main',
  srcs = ["main.py"],
  deps = [
    "//utilities:logger",
    "//utilities:memory",
  ],
)
