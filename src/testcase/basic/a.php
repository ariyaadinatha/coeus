<?php
$intList = array(4,1,6,5,3,2);
$maxNum = -1;

// find biggest int
foreach ($intList as $i) {
   if ($i > $maxNum) {
       $maxNum = $i;
   }
}

echo $maxNum;
?>