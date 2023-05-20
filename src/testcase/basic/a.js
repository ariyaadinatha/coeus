let intList = [4,1,6,5,3,2];
let maxNum = -1;

// find biggest int
for (let i of intList) {
   if (i > maxNum) {
       maxNum = i;
    }
}

console.log(maxNum);