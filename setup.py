import os
import setuptools
from Cython.Build import cythonize

# Tìm tất cả các file .py trong thư mục app/
python_files = []
for root, dirs, files in os.walk("app"):
    for file in files:
        if file.endswith(".py") and not file.startswith("__"):
            python_files.append(os.path.join(root, file))

setuptools.setup(
    ext_modules=cythonize(
        python_files,
        compiler_directives={"language_level": "3"},
    )
)