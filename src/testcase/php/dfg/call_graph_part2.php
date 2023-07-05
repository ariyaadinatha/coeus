<?php
require __DIR__ . '/File1.php';
$test = $_GET[ 'id' ];
echo first($test, "omg lol"); //returns omg lol;