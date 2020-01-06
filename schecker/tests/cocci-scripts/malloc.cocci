// find calls to malloc
@call@
expression ptr;
position p;
@@

ptr@p = malloc(...);

// find ok calls to malloc
@ok@
expression ptr;
position call.p;
@@

ptr@p = malloc(...);
... when != ptr
(
 (ptr == NULL || ...)
|
 (ptr != NULL || ...)
)

// fix bad calls to malloc
@depends on !ok@
expression ptr;
position call.p;
@@

ptr@p = malloc(...);
+ if (!ptr)
+     xabort('no memory; gracefull handle situation now');
