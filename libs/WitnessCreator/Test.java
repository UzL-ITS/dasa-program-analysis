import org.sosy_lab.sv_benchmarks.Verifier;
public class Test {
    public static void main(String[] args) {
        int x = Verifier.nondetInt();
        int y = Verifier.nondetInt();
        int z = 0;
        try {
            z += calc(x, y);
        } catch (ArithmeticException e) {
            assert  false;
        }
        if (z > 20) assert false;
    }

    public static int calc(int a, int b) {
        int q = a / b;
        q = calc(a, b - q);
        return q;
    }
}
