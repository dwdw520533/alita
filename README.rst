Alita
=====

一个轻量级的Web异步服务器框架，需要Python3.4+版本。


Installing
----------

.. code-block:: text

    pip install -r requirements.txt


A Simple Example
----------------

.. code-block:: python

    from alita import Alita

    app = Alita()

    @app.route('/')
    async def hello(request):
        return 'Hello, World!'

.. code-block:: text

Start
-----

命令行启动Alita服务器。

Links
-----

* Code: https://github.com/dwdw520533/alita
