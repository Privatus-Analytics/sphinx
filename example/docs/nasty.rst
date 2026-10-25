Nasty
=====

The page props go through the extension (see conf.py). Sphinx has no event
helper, so the button's attribute is written in raw HTML with HTML entities.

.. raw:: html

   <button type="button" data-privatus-event="Nasty value" data-privatus-prop-nasty="&lt;/script&gt;&lt;script&gt;window.__pwned=1&lt;/script&gt;&#x2028;&#x2029;&amp;&lt;&gt;&quot;&#39;">Nasty</button>
