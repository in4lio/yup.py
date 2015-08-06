
/*  co.c was generated by yup.py (yupp) 0.8b8
    out of co.yu-c at 2015-08-06 16:25
 *//**
 *  \file  co.c (co.yu-c)
 *  \brief  Coroutines implementation.
 *  \author  Vitaly Kravtsov (in4lio@gmail.com)
 *  \copyright  See the LICENSE file.
 */

#define CO_IMPLEMENT

#include <stdio.h>
#include "co.h"

static semaphore_t eol;

#define SQ  19  /* odd, square side length */
static int spiral[ SQ * SQ ] = { 0 };

void init_spiral( void )
{
	const int dp[ 4 ] = { -SQ, -1, SQ, 1 };  /* step up, left, down and right */
	int p = SQ * SQ / 2;  /* position in spiral */
	int n = 2;  /* current number */
	int lch = 3;  /* chain length */
	int i, ii;

	spiral[ p ] = 1;
	spiral[ ++p ] = 2;
	while ( n < SQ * SQ ) {
		for ( i = 0; i < 4; i++ ) {  /* up-left-down-right cycle */
			for ( ii = 0; ii < lch >> 1; ii++ ) {  /* chain cycle */
				p += dp[ i ];
				spiral[ p ] = ++n;
			}
			++lch; /* chain grows up every second turn */
		}
	}
}

int isprime( int n )
{
	int i;

	if ( n == 2 ) return 1;
	if ( n == 1 || n % 2 == 0 ) return 0;
	for ( i = 3; i * i <= n; i += 2 ) if (( n % i ) == 0 ) return 0;
	return 1;
}

int A_init( void )
{
	init_spiral();
	return ( CO_READY );
}

void A_uninit( void )
{

}

CORO_DEFINE( A )
{
	CORO_LOCAL int i;

	CORO_BEGIN();
	/* begin */
	for ( i = 0; i < SQ * SQ; i++ ) {
		/* ulam spiral */
		if ( isprime( spiral[ i ])) {
			printf( "%03d", spiral[ i ]);
		} else {
			printf( " . " );
		}
		CORO_YIELD();
	}
	/* end */
	CORO_END();
}

int B_init( void )
{
	return ( CO_READY );
}

void B_uninit( void )
{

}

CORO_DEFINE( B )
{
	CORO_LOCAL int i;

	CORO_BEGIN();
	/* begin */
	while ( CORO_ALIVE( A_alive ) ) {
		SEMAPHORE_ACQUIRE( eol,);
		for ( i = 0; i < SQ - 1; i++ ) {
			/* spacing */
			printf( " " );
			CORO_YIELD();
		}
		SEMAPHORE_RELEASE( eol );
		CORO_YIELD();
	}
	/* end */
	CORO_END();
}

int C_init( void )
{
	SEMAPHORE_INIT( eol, 1 );
	return ( CO_READY );
}

void C_uninit( void )
{

}

CORO_DEFINE( C )
{
	
	CORO_BEGIN();
	/* begin */
	while ( CORO_ALIVE( A_alive ) ) {
		SEMAPHORE_ACQUIRE( eol,);
		/* line breaking */
		printf( "\n" );
		SEMAPHORE_RELEASE( eol );
		CORO_YIELD();
	}
	/* end */
	CORO_END();
}
