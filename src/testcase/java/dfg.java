import java.util.Scanner;

public class DataFlow {

    public static void main(String[] args) {
        String test = "test";
        String anotherTest = test;

        if(true){
            test = "change 1";
            System.out.println(test);
        }
        else if (false) {
            test = "change 2";
            System.out.println(test);
        }
        else{
            test = "change 3";
            System.out.println(test);
        }

        System.out.println(test);
        System.out.println(anotherTest);
    }
}