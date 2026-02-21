Farb- und Typografie-Token
==========================

Quelle
------

Die UI-Tokens werden in ``app/static/css/theme.css`` im ``@theme``-Block definiert.

Schrift
-------

- Sans-Serif-Stack: ``Inter Variable`` als Primärfont
- Token: ``--font-sans``

Farbpaletten
------------

Grün (Primärpalette, Flowbite-kompatibel)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Token
     - Hex
   * - ``--color-green-50``
     - ``#F3FAF7``
   * - ``--color-green-100``
     - ``#DEF7EC``
   * - ``--color-green-200``
     - ``#BCF0DA``
   * - ``--color-green-300``
     - ``#84E1BC``
   * - ``--color-green-400``
     - ``#31C48D``
   * - ``--color-green-500``
     - ``#0E9F6E``
   * - ``--color-green-600``
     - ``#057A55``
   * - ``--color-green-700``
     - ``#046C4E``
   * - ``--color-green-800``
     - ``#03543F``
   * - ``--color-green-900``
     - ``#014737``

Grau
^^^^

.. list-table::
   :header-rows: 1

   * - Token
     - Hex
   * - ``--color-gray-50``
     - ``#f9fafb``
   * - ``--color-gray-100``
     - ``#f3f4f6``
   * - ``--color-gray-200``
     - ``#e5e7eb``
   * - ``--color-gray-300``
     - ``#d1d5db``
   * - ``--color-gray-400``
     - ``#9ca3af``
   * - ``--color-gray-500``
     - ``#6b7280``
   * - ``--color-gray-600``
     - ``#4b5563``
   * - ``--color-gray-700``
     - ``#374151``
   * - ``--color-gray-800``
     - ``#1f2937``
   * - ``--color-gray-900``
     - ``#111827``

Weitere Tokens
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Palette
     - Token
     - Hex
   * - Rot
     - ``--color-red-500``
     - ``#ef4444``
   * - Rot
     - ``--color-red-600``
     - ``#dc2626``
   * - Rot
     - ``--color-red-700``
     - ``#b91c1c``
   * - Rot
     - ``--color-red-900``
     - ``#7f1d1d``
   * - Blau
     - ``--color-blue-500``
     - ``#3b82f6``
   * - Blau
     - ``--color-blue-600``
     - ``#2563eb``
   * - Gelb
     - ``--color-yellow-500``
     - ``#eab308``
   * - Gelb
     - ``--color-yellow-600``
     - ``#ca8a04``
   * - Amber
     - ``--color-amber-50``
     - ``#fffbeb``
   * - Amber
     - ``--color-amber-200``
     - ``#fde68a``
   * - Amber
     - ``--color-amber-500``
     - ``#f59e0b``
   * - Amber
     - ``--color-amber-800``
     - ``#92400e``

Hinweis zu Änderungen
---------------------

Tokenänderungen in ``theme.css`` wirken global auf Templates und Komponenten.
Nach Tokenänderungen:

.. code-block:: bash

   bun run build
