<?php
function first($int, $string){ //function parameters, two variables.
    $query = "SELECT first_name, last_name FROM users WHERE user_id = '$int';";
    $result = mysqli_query($GLOBALS["___mysqli_ston"],  $query );
}