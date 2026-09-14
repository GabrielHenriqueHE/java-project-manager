package com.example.api;

import com.example.core.Core;

public class Api {
    public String hello() {
        return new Core().greet();
    }
}
