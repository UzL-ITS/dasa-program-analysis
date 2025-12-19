import org.sosy_lab.sv_benchmarks.Verifier;

class Main {


    public static void main(String[] args) {
        int i = Verifier.nondetInt();

        if (i <= 10) assert false : "i is smaller 10"; // should fail
        System.out.println("No Failure detected");
    }


}