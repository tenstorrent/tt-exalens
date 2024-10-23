#ifndef UNPACK_KERNELS_H
#define UNPACK_KERNELS_H

    #include <cstdint>
    #include <cstdarg>

    #define PROCESS_NUMBERS(n, ...) processNumbers(n, __VA_ARGS__)

    void unpack_A_kernel();
    void unpack_AB_kernel();
    void nop();
    extern void(*kernels[10])(void);

    /* Function for assigning elemtens of kernerls array to some of kernels */
    inline void processNumbers(int n, int first, ...) {

        // Set the first kernel based on the first argument
        if(first == 1){
            kernels[0] = &unpack_A_kernel;
        } else if(first == 2){
            kernels[0] = &unpack_AB_kernel;
        } else {
            kernels[0] = &nop;
        }

        va_list args;
        va_start(args, first);
        for (int i = 1; i < n; ++i) {
            int num = va_arg(args, int);
            if(num == 1){
                kernels[i] = &unpack_A_kernel;
            } else if(num == 2){
                kernels[i] = &unpack_AB_kernel;
            } else {
                kernels[i] = &nop;
            }
        }
        va_end(args);
    }

#endif