public class FindMax {

    public static void main(String[] args) {
        int[] intList = {4, 1, 6, 5, 3, 2};
        int maxNum = -1;

        // find biggest int
        for (int i = 0; i < intList.length; i++) {
            if (intList[i] > maxNum) {
                maxNum = intList[i];
            }
        }

        System.out.println(maxNum);
    }
}