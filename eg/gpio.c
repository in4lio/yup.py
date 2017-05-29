/*  gpio.c was generated by yup.py (yupp) 1.0c2
    out of gpio.yu-c 
 *//**
 *  \file  gpio.c (gpio.yu-c)
 *  \brief  Generic example of using preprocessor for interaction with GPIO pins.
 */

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>

/**
 *  \defgroup periph Simulation of peripheral registers
 *  \{
 */

/**
 *  \defgroup reg_mode GPIO MODE register
 *  \{
 */

#define GPIO_MODE_INPUT   0
#define GPIO_MODE_OUTPUT  1

#define GPIO_MODE_PIN0  0
#define GPIO_MODE_PIN1  1
#define GPIO_MODE_PIN2  2
#define GPIO_MODE_PIN3  3
#define GPIO_MODE_PIN4  4
#define GPIO_MODE_PIN5  5
#define GPIO_MODE_PIN6  6
#define GPIO_MODE_PIN7  7
#define GPIO_MODE_PIN8  8
#define GPIO_MODE_PIN9  9
#define GPIO_MODE_PIN10  10
#define GPIO_MODE_PIN11  11
#define GPIO_MODE_PIN12  12
#define GPIO_MODE_PIN13  13
#define GPIO_MODE_PIN14  14
#define GPIO_MODE_PIN15  15

/** \} */

/**
 *  \defgroup reg_pull GPIO PULL register
 *  \{
 */

#define GPIO_PULL_OFF   0
#define GPIO_PULL_UP    1
#define GPIO_PULL_DOWN  2

#define GPIO_PULL_PIN0  0
#define GPIO_PULL_PIN1  2
#define GPIO_PULL_PIN2  4
#define GPIO_PULL_PIN3  6
#define GPIO_PULL_PIN4  8
#define GPIO_PULL_PIN5  10
#define GPIO_PULL_PIN6  12
#define GPIO_PULL_PIN7  14
#define GPIO_PULL_PIN8  16
#define GPIO_PULL_PIN9  18
#define GPIO_PULL_PIN10  20
#define GPIO_PULL_PIN11  22
#define GPIO_PULL_PIN12  24
#define GPIO_PULL_PIN13  26
#define GPIO_PULL_PIN14  28
#define GPIO_PULL_PIN15  30

/** \} */

/**
 *  \defgroup reg_filt GPIO FILT register
 *  \{
 */

#define GPIO_FILT_OFF  0
#define GPIO_FILT_ON   1

#define GPIO_FILT_PIN0  0
#define GPIO_FILT_PIN1  1
#define GPIO_FILT_PIN2  2
#define GPIO_FILT_PIN3  3
#define GPIO_FILT_PIN4  4
#define GPIO_FILT_PIN5  5
#define GPIO_FILT_PIN6  6
#define GPIO_FILT_PIN7  7
#define GPIO_FILT_PIN8  8
#define GPIO_FILT_PIN9  9
#define GPIO_FILT_PIN10  10
#define GPIO_FILT_PIN11  11
#define GPIO_FILT_PIN12  12
#define GPIO_FILT_PIN13  13
#define GPIO_FILT_PIN14  14
#define GPIO_FILT_PIN15  15

/** \} */

/**
 *  \defgroup reg_state GPIO STATE register
 *  \{
 */

#define GPIO_STATE_PIN0  0
#define GPIO_STATE_PIN1  1
#define GPIO_STATE_PIN2  2
#define GPIO_STATE_PIN3  3
#define GPIO_STATE_PIN4  4
#define GPIO_STATE_PIN5  5
#define GPIO_STATE_PIN6  6
#define GPIO_STATE_PIN7  7
#define GPIO_STATE_PIN8  8
#define GPIO_STATE_PIN9  9
#define GPIO_STATE_PIN10  10
#define GPIO_STATE_PIN11  11
#define GPIO_STATE_PIN12  12
#define GPIO_STATE_PIN13  13
#define GPIO_STATE_PIN14  14
#define GPIO_STATE_PIN15  15

/** \} */

/**
 *  \defgroup reg_clock GPIO clock register
 *  \{
 */

#define GPIO_CLOCK_PORTA  0
#define GPIO_CLOCK_PORTB  1
#define GPIO_CLOCK_PORTC  2

uint32_t GPIO_CLOCK;

/** \} */

/**
 *  \defgroup reg_port GPIO port registers
 *  \{
 */

typedef struct {
	uint32_t mode;
	uint32_t pull;
	uint32_t filt;
	uint32_t state;
} GPIO_PORT;

GPIO_PORT PORTA, PORTB, PORTC;

/** \} */

/** \} */

/**
 *  \defgroup inputs Functions for interaction with inputs
 *  \{
 */

/**
 *  \brief Identifiers of inputs.
 */
enum {
	NACK,
	BUSY,
	PE,
	SLCT,
	NERR,

	IN__COUNT_  /**< Count of inputs. */
};

/**
 *  \brief Initialize GPIO ports.
 */
void init_gpio( void )
{
	/* Enable GPIO clocks */
	GPIO_CLOCK |= 0 | ( 1UL << GPIO_CLOCK_PORTA ) | ( 1UL << GPIO_CLOCK_PORTB ) | ( 1UL << GPIO_CLOCK_PORTC );

	/* Configure GPIO ports */
	PORTA.mode = ( 0
		| ( GPIO_MODE_INPUT << GPIO_MODE_PIN0 )
		| ( GPIO_MODE_INPUT << GPIO_MODE_PIN3 )

	);
	PORTA.pull = ( 0
		| ( GPIO_PULL_DOWN << GPIO_PULL_PIN0 )
		| ( GPIO_PULL_OFF << GPIO_PULL_PIN3 )

	);
	PORTA.filt = ( 0
		| ( GPIO_FILT_OFF << GPIO_FILT_PIN0 )
		| ( GPIO_FILT_ON << GPIO_FILT_PIN3 )

	);
	PORTB.mode = ( 0
		| ( GPIO_MODE_INPUT << GPIO_MODE_PIN1 )
		| ( GPIO_MODE_INPUT << GPIO_MODE_PIN2 )

	);
	PORTB.pull = ( 0
		| ( GPIO_PULL_OFF << GPIO_PULL_PIN1 )
		| ( GPIO_PULL_UP << GPIO_PULL_PIN2 )

	);
	PORTB.filt = ( 0
		| ( GPIO_FILT_ON << GPIO_FILT_PIN1 )
		| ( GPIO_FILT_OFF << GPIO_FILT_PIN2 )

	);
	PORTC.mode = ( 0
		| ( GPIO_MODE_INPUT << GPIO_MODE_PIN4 )

	);
	PORTC.pull = ( 0
		| ( GPIO_PULL_DOWN << GPIO_PULL_PIN4 )

	);
	PORTC.filt = ( 0
		| ( GPIO_FILT_OFF << GPIO_FILT_PIN4 )

	);

}

/**
 *  \brief Get state of NACK input.
 *  \return State.
 */
bool get_NACK( void )
{
	return (( PORTA.state & GPIO_STATE_PIN2 ) != 0 );  /* port A pin 2 */
}

/**
 *  \brief Get state of BUSY input.
 *  \return State.
 */
bool get_BUSY( void )
{
	return (( PORTB.state & GPIO_STATE_PIN11 ) != 0 );  /* port B pin 11 */
}

/**
 *  \brief Get state of PE input.
 *  \return State.
 */
bool get_PE( void )
{
	return (( PORTB.state & GPIO_STATE_PIN13 ) != 0 );  /* port B pin 13 */
}

/**
 *  \brief Get state of SLCT input.
 *  \return State.
 */
bool get_SLCT( void )
{
	return (( PORTA.state & GPIO_STATE_PIN5 ) != 0 );  /* port A pin 5 */
}

/**
 *  \brief Get state of NERR input.
 *  \return State.
 */
bool get_NERR( void )
{
	return (( PORTC.state & GPIO_STATE_PIN7 ) != 0 );  /* port C pin 7 */
}

bool get_input( int in )
{
	switch ( in ) {
	case NACK:
		return get_NACK();
	case BUSY:
		return get_BUSY();
	case PE:
		return get_PE();
	case SLCT:
		return get_SLCT();
	case NERR:
		return get_NERR();

	}
	return false;
}

/** \} */

int main( void )
{
	init_gpio();

	bool nack = get_input( NACK );
	bool busy = get_input( BUSY );
	bool pe = get_input( PE );
	bool slct = get_input( SLCT );
	bool nerr = get_input( NERR );

	printf( "NACK = %d\n", get_NACK());
	printf( "BUSY = %d\n", get_BUSY());
	printf( "PE = %d\n", get_PE());
	printf( "SLCT = %d\n", get_SLCT());
	printf( "NERR = %d\n", get_NERR());

}
