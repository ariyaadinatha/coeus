<?php
$a = "value";
$b = "other";

$temp = $a;
$a = $b;
$b = $temp;

echo $a;
echo $b;