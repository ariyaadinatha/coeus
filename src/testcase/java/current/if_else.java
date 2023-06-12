import java.util.Scanner;

public class EvenOdd {

    public static void main(String[] args) {

        Scanner reader = new Scanner(System.in);

        System.out.print("Enter a number: ");
        int num = reader.nextInt();

        if(num % 2 == 0){
            System.out.println(num + " is even");
        }
        else if (num % 3 == 0) {
            System.out.println(num + " is 3 multiplier");
        }
        else{
            System.out.println(num + " is idk");
        }
    }
}