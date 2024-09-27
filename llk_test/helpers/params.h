#ifndef PARAMS_H
#define PARAMS_H

#ifdef LLK_TRISC_UNPACK

    #ifdef FORMAT_FLOAT16_B
        #define DATA_FORMAT (uint32_t)DataFormat::Float16_b
    #endif
    #ifdef FORMAT_FLOAT16
        #define DATA_FORMAT (uint32_t)DataFormat::Float16
    #endif
    #ifdef FORMAT_FLOAT32
        #define DATA_FORMAT (uint32_t)DataFormat::Float32
    #endif
    #ifdef FORMAT_INT32
        #define DATA_FORMAT (uint32_t)DataFormat::Int32
    #endif

#endif

#ifdef LLK_TRISC_MATH

    #ifdef ELTWISE_BINARY_ADD
        #define ELTWISE_BINARY_OP EltwiseBinaryType::ELWADD
    #endif
    #ifdef ELTWISE_BINARY_SUB
        #define ELTWISE_BINARY_OP EltwiseBinaryType::ELWSUB
    #endif
    #ifdef ELTWISE_BINARY_MUL
        #define ELTWISE_BINARY_OP EltwiseBinaryType::ELWMUL
    #endif

#endif

#ifdef LLK_TRISC_PACK

    #ifdef FORMAT_FLOAT16_B
        #define DATA_FORMAT (uint32_t)DataFormat::Float16_b
    #endif
    #ifdef FORMAT_FLOAT16
        #define DATA_FORMAT (uint32_t)DataFormat::Float16
    #endif
    #ifdef FORMAT_FLOAT32
        #define DATA_FORMAT (uint32_t)DataFormat::Float32
    #endif
    #ifdef FORMAT_INT32
        #define DATA_FORMAT (uint32_t)DataFormat::Int32
    #endif

#endif

#endif