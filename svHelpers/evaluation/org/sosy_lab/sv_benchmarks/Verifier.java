// This file is part of the SV-Benchmarks collection of verification tasks:
// https://github.com/sosy-lab/sv-benchmarks
//
// SPDX-FileCopyrightText: Contributed by Peter Schrammel
// SPDX-FileCopyrightText: 2011-2020 The SV-Benchmarks Community
//
// SPDX-License-Identifier: Apache-2.0

package org.sosy_lab.sv_benchmarks;

import java.util.Scanner;
import java.util.HashMap;
import java.util.Base64;

public final class Verifier {
    private static final HashMap<Integer, String> input_map = new HashMap<>();
    private static boolean initialized = false;
    private static int counter = 0;

    private static void initialize() {
        Scanner sc  = new Scanner(System.in);
        while (sc.hasNextLine()) {
            String line = sc.nextLine();
            input_map.put(Integer.parseInt(line.split(" ")[0].split("_")[1]), line.split(" ")[1]);
        }
        sc.close();
        initialized = true;
    }

    public static void assume(boolean condition) {
        if (!condition) {
            Runtime.getRuntime().halt(1);
        }
    }

    public static boolean nondetBoolean() {
        if (!initialized) initialize();
        return Boolean.parseBoolean(input_map.get(counter++));
    }

    public static byte nondetByte() {
        if (!initialized) initialize();
        String s = input_map.get(counter++);
        if (s == null){
            System.out.println("[CANNOT PARSE NULL STRING]");
            return 0;
        }
        return Byte.parseByte(s);
    }

    public static char nondetChar() {
        String s = nondetString();
        return s.charAt(0);
    }

    public static short nondetShort() {
        if (!initialized) initialize();
        String s = input_map.get(counter++);
        if (s == null){
            System.out.println("[CANNOT PARSE NULL STRING]");
            return 0;
        }
        return Short.parseShort(s);
    }

    public static int nondetInt() {
        if (!initialized) initialize();
        String s = input_map.get(counter++);
        if (s == null){
            System.out.println("[CANNOT PARSE NULL STRING]");
            return 0;
        }
        return Integer.parseInt(s);
    }

    public static long nondetLong() {
        if (!initialized) initialize();
        String s = input_map.get(counter++);
        if (s == null){
            System.out.println("[CANNOT PARSE NULL STRING]");
            return 0;
        }
        return Long.parseLong(s);
    }

    public static float nondetFloat() {
        if (!initialized) initialize();
        String s = input_map.get(counter++);
        if (s == null){
            System.out.println("[CANNOT PARSE NULL STRING]");
            return 0;
        }
        return Float.parseFloat(s);
    }

    public static double nondetDouble() {
        if (!initialized) initialize();
        String s = input_map.get(counter++);
        if (s == null){
            System.out.println("[CANNOT PARSE NULL STRING]");
            return 0;
        }
        return Double.parseDouble(s);
    }

    public static String nondetString() {
        if (!initialized) initialize();
        String s = input_map.get(counter++);
        if (s == null) {
            System.out.println("[CANNOT PARSE NULL STRING]");
            return "DASA";
        }
        s = new String(Base64.getDecoder().decode(s));
        return s;
    }
}
