<?php
function first($int) { //function parameters, two variables.
    return "SELECT first_name, last_name FROM users WHERE user_id = '$int';";
}

function second($query) {
    mysqli_query($GLOBALS["___mysqli_ston"],  $query );
}

$test = $_GET[ 'id' ];
$query = first($test);
echo second($query); //returns omg lol;