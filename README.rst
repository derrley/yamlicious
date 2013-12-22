Yamlicious is a (work-in-progress) lightweight configuration library built on
top of YAML. It's for folks who love to write their configuration files in
YAML, but who find themselves writing additional boilerplate each time they
want to use YAML for configuration files.

Seems like every time you want to use YAML for config, you have to write code
that:

- Validates the correctness of a file and prints an understandable failure
  message when the file doesn't quite match

- Understands your environemnt, and allows you to configure different properties
  for different environment dimensions without unnecessary DRY-violation

- Reads configuration from multiple files

- Provides a cascading set of configuration sources, including environment
  variables.

- Lazily loads certain parts of a large configuration. (read: when your
  "configuration" really starts to feel more like "data.")

Yamlicious does all this by being like any other YAML parser, but by treating a
handful of specific keys (prefixed with the underscore) in a special way. It
can be configured to recognize and evaluate any subset of these *feature keys*,
allowing a developer to bake in as much (or as little!) of the crazy
capabilities as seems reasonable for the situation. In fact, the craziest stuff
is turned off by default. :)

Skip to `Feature Key Definitions`_ if you want the formality without the
English verbiage.

.. contents::


The Yamlicious File
====================

A configuration file specified in Yamlicious *is just YAML*. In fact, nothing stops
you from parsing a Yamlicious file with any YAML library (unlike other solutions,
which use template languages on top of YAML.). This can be useful for
searching, cleaning, or editing (with syntax highlighting) the file.


Environment Variable Subtitution
---------------------------------

Yamlicious gives your configuration file automatic access to the environment. Just
pretend like every string you write in YAML is ``format()`` ed with ``os.environ``.

.. code-block:: yaml

  some:
    key:
      user_{USER}: not cool
      user_kyle: cool

Don't worry. The Yamlicious API gives you (the developer) the ability to both
limit the environment variables your configuration file is allowed to access
and provide overriding values for anything in the environment. You're neither
forced to use environment variables nor doomed to a free for all.

Yamlicious supports list values in the environment, and splits environment variables
on the comma character. If a Yamlicious file substitutes a list variable into a
string, that string renders into multiple strings (one for each value in the
list variable).

List substitution behavior varies subtly by situation.


When substituting into a single value string
````````````````````````````````````````````

.. code-block:: yaml

  some_list: {MY_LIST}

renders to the following, if ``MY_LIST=one,two,three`` is in the environment.

.. code-block:: yaml

  some_list:
    - one
    - two
    - three

If the variable is not set, renders ``None``.


When substituting into a value list
```````````````````````````````````

.. code-block:: yaml

  some_list:
    - first
    - {LIST}

becomes

.. code-block:: yaml

  some_list:
    - first
    - one
    - two
    - three

If the variable is not set, simply adds nothing to the list.


When substituting into a key string
```````````````````````````````````

Key strings are special, because you almost certainly don't intend to make a
list into the key of a dictionary. Instead, you likely mean to define a key in
the dictionary for each item in the list. Yamlicious provides a special
variable in the environment, ``_KEY``, to help you out in this situation.

.. code-block:: yaml

  {LIST}: {_KEY} is in the list!

becomes

.. code-block:: yaml

  one: one is in the list
  two: two is in the list
  three: three is in the list

If the variable is not set, adds no keys to the document.


When substituting multiple list values into the same string
````````````````````````````````````````````````````````````

This is interpreted as a dot product. Yamlicious will substitute every combination of
variables between the two lists.

If ``BOYS=joey,johnny,bobby`` and ``GIRLS=sally,mary`` then:

.. code-block:: yaml

  "{BOYS} likes {GIRLS}"

becomes:

.. code-block:: yaml

  - joey likes sally
  - joey likes mary
  - johnny likes sally
  - jonny likes mary
  - bobby likes sally
  - bobby likes mary

Note -- the rest of the "positional" list substitution rules (defined in the
immediately previous sections) apply to dot product substitutions.


Load Another File
----------------------

Sometimes, it makes sense to define configuration in more than one place.
Yamlicious gives you the `_include`_ key to accomplish this. (Note that
relative paths are from python's current working directory, but you can
override this in the Yamlicious API.)

.. code-block:: yaml

  some_place:
    placed_here:
      _include: other/file.yaml

In this case, the rendered YAML output of ``other/file.yaml`` is placed under
the ``placed_here`` key.

.. code-block:: yaml

  some_place:
    placed_here:
      contents of:
        - that other file
        - which can be arbitrary YAML

You can use variable substitution with the file include feature to get
conditional configuration.

.. code-block:: yaml

  user_settings:
    _include: {USER}/conf.yaml


Merge
---------------

Yamlicious allows you to *merge* an external file into a bit of config.

.. code-block:: yaml

  merged_settings:
    _merge:
      - some_list: ['thing']
        some_thing: 'thing'

      - _include: some_other_place.yaml

When you ask Yamlicious to do this, it will use a strategy I call *safe deep merge
with list append*. Yamlicious merges dictionaries recursively by combining their
key-value pairs. It merges lists by list addition. It refuses, however, to
merge anything else. (Anything else would be shoot-self-in-foot territory, and
I'd rather not encourage it.)

if ``some_other_place.yaml`` looked like this:

.. code-block:: yaml

  some_list: ['second_thing']
  some_other_thing: 'thing'


The above configuration would render as follows:

.. code-block:: yaml

  merged_settings:
    some_list: ['thing', 'second_thing']
    some_thing: 'thing'
    some_other_thing: 'thing'

If you're looking to implement the common *default override* pattern, specify
`The Default Document`_ as part of the Yamlicious API. That feature is specifically
built to help you not have to allow arbitrary overrides when including files.
If you absolutely must allow overrides, use the `_merge_override`_ keyword,
but note that it is turned off by default.

Include and Merge
------------------

Loading several files and merging them is a common pattern, and it would be
nice if folks didn't have to be verbose if that's the behavior they're looking
for. This is what the `_include_merge`_ key is for.

.. code-block:: yaml

  merged_stuff:
    _include_merge:
      - first/place.yaml
      - second/place.yaml
      - third/place.yaml

This key will load each file in order and merge that file into the previous
file.


The Environment's Key
-------------------------

Just so that it's explicit, Yamlicious includes a special key into the document that
it returns, `_env`_, that maps to a dictionary of environment variables that
were set when Yamlicious rendered the configuration file.

You can also use the `_env`_ key to set environment variables. It behaves just
like any other key, except any key set underneath automatically makes its way
into the environment. Other than that, there's nothing special about `_env`_.
Feel free to use string substitution in the keys or values.

.. code-block:: yaml

  _env:
    {COOL_NAMES}: Sir {_KEY}-a-lot

The `_env`_ key is treated a bit special by the file includer. Rather than
actually drop it into the middle of a document, it merges the environment of
the included document into the environment of the including document.  This has
meaningful ramifications. If you're using string substitution to conditionally
include a document, you can set variables in the `_env`_ key of said document
that affect to the rest of the Yamlicious configuration parsing process (including,
for example, variables that by being set cause additional other files to be
loaded). String substitution, file inclusion, and environment merging are the
primary (and recommended) ways to make your configuration files conditional
without giving them too much expressive power.


The Default Document
---------------------

Yamlicious merge-overrides the configuration document it renders with a
*default document* that it is configured to use. The `_env`_ key of the
default document is set to the environment that's bound at the beginning of
configuration processing. The environment is initialized by merge-overriding
the environment specificed in the Yamlicious API on top of the system's actual
environment variables.

Use the default document to specify default values. It's cleaner to bake these
values into your python codebase, and specify them as part of the API, than it
is to develop a ``_merge_override`` strategy for loading additional
configuration files.


Functional Conditional Keys
---------------------------------

To specify a condition in-line, you can use the *functional conditional*
feature keys (`_case`_ and `_cond`_), each inspired by Lisp. (No project is
complete without a smidge of functional programming.) This adds a bit too much
Turing completeness to the project for the taste of most, so these are disabled
by default.

.. code-block:: yaml

  case_configuration:
    '_case':
      - '{USER}'
      - {'kyle': 'is awesome'}
      - {'_otherwise': 'is not awesome'}
  cond_configuration:
    '_cond':
      - {"{ENV} in ['test', 'prod']": 'go!'}
      - {true: 'undefined'}

Note the use of the python expression. This is mostly for convenience and
terseness. Nobody wants to write a boolean expression in YAML, and I don't
particularly want to implement it, either, so Yamlicious ``eval()`` s every single
string that it finds below either functional conditional key.

Keep the processing order in mind.

- string substitution
- python evaluation
- `_case`_ / `_cond`_ evaluation.

List substitution works in both kinds of functional conditional. For example,
if ``GOOD_USERS=kyle,anthony``, then the following expression

.. code-block:: yaml

  access_configuration:
    '_case':
      - {'{GOOD_USERS}': 'go!'}
      - {'_otherwise':  'stay. :('}

evaluates to

.. code-block:: yaml

  access_configuration:
    '_case':
      - {'kyle': 'go!',
         'anthony': 'go!'}
      - ['_otherwise',  'stay. :(']

Yamlicious is careful to "do the right thing" here. While there is no defined
order in how it matches either the key ``'anthony'`` or ``'kyle'``, it will try
to match both before falling back to the `_otherwise`_ key.

Be careful to not do something like this unless you really mean it:

.. code-block:: yaml

  access_configuration:
    '_case':
      - {'{GOOD_USERS}': '{_KEY}'}
      - {'_otherwise':  'stay. :('}

While it will technically work, Yamlicious offers no definition for what the
above expression evaluates to.


Lazy Loading
--------------

If you notice an explosion in the number of Yamlicious files that your program
includes, and you also notice that only a few of them ever get used, you'll
likely want to conditionally load said files only when they're needed. Yamlicious
provides two lazy loading keys to help you with this.

The `_lazy`_ key changes nothing about the semantic meaning of the document it
points to, except that the document's validation happens when it is accessed
rather than at the time that configuration is loaded. 

The `_lazy_lookup`_ key allows you to use string substitution of the special
variable ``{_KEY}`` to define how every key in the document is looked up.

To get the most power, pair lazy lookup with file inclusion and list
substitution. Here's an example inspired by YAML configuration of SQL tables.

.. code-block:: yaml

  tables:
    _lazy_lookup:
      _include_merge:
        - generic/schema/{_KEY}.table.yaml
        - {SYSTEM}/schema/{_KEY}.table.yaml
        - {INSTITUTION}/schema/{_KEY}.table.yaml

Note that there's nothing that prevents lazy-loaded documents from merging with
one another. If you're feeling particularly masochistic, you can define this
confusing yet equivalent thing.

.. code-block:: yaml

  tables:
    _merge:
      - _lazy_lookup:
          _include_merge:
            - generic/schema/{_KEY}.table.yaml
            - {SYSTEM}/schema/{_KEY}.table.yaml
      - _lazy_lookup:
          _include_merge:
            - {INSTITUTION}/schema/{_KEY}.table.yaml


Feature Key Definitions
========================

Enough with your words. Let's define this stuff explicitly.

Every feature key exists to denote that some specific behavior be applied
to a YAML document. The key must exist by itself in its containing dictionary,
and its value describes the document that the operation operates on.

.. code-block:: yaml

  _<feature-key>: <document>


_env 
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

  _env:
    <variable>: <value>
    ...

Evaluates to itself, but has the side effect of setting environment variables
to values in the *global* scope. Not specific to a single subdocument.


_include
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

  _include: <file-path>

Evaluates to the loaded and processed configuration document found at
``file_path``.


_merge
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

  _merge: [ <document>, <document>, ... ]

Uses safe-merge-with-list-append to merge given documents together. Can safely
merge dictionaries and lists, but nothing else.


_merge_override
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

  _merge_override: [ <document>, <document>, ... ]

Uses deep-merge to merge given documents together. Can safely merge anything.
For scalar values, documents further down the list override documents earlier
in the list.


_include_merge
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

  _include_merge [ <file-path>, <file-path>, ... ]

Loads files and then merges them with safe-merge-with-list-append.


_case
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

  '_case':
    - <key-python-expression>
    - {<match-python-expression>, <outcome-python-expression>}
    ...

Functional case. Evaluates to the first outcome expression whose match
expression is python-equal to the key expression.


_otherwise
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_otherwise': <expression>

Evaluates to a case condition that always matches.


_cond
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_cond':
      - {<boolean-python-expression>, <outcome-python-expression>}
      ...

Functional cond. Evaluates to the first outcome expression whose boolean
expression is true.


_lazy
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_lazy': <document>

Evaluates to document, but where each of the keys in document is lazy-loaded.


_lazy_lookup
----------------------------------
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_lazy_lookup': <value-expression>

Evaluates to a lazy-loaded dictionary, where every key is evaluated at lookup
time by evaluating the value-expression, which is allowed to use the ``_KEY``
environment variable


The Validator
==============

TBD

The Command
====================

TBD

The API
=================

TBD

Custom Feature Keys
====================

TBD
