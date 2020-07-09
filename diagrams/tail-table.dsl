// https://dbdiagram.io/

Table LAYER_X as L {
  OBJECTID int [pk, increment]
  TAILID int [unique, increment]
  "..." any
}

Table LAYER_X_TAIL1 as T {
  TAILID int [ref: - LAYER_X.TAILID]
  "..." any
}

Table LAYER_X_TAIL_PERMISSIONS as T {
  TAIL_FQN text [pk]
  GROUP_ID text [pk]
}
