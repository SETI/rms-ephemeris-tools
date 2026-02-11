/*******************************************************************************
* kepler.h -- Include file for the Kepler Library
*
* Mark R. Showalter, 15 April 1991
* Updated 12 September 2005
*******************************************************************************/

/*******************************************************************************
* Type definitions
*******************************************************************************/

#define NJ_MAX 10	/* Allows for J2--J20 */

typedef struct {
	double		radius, radius2;
	double		GM, GMoverR3;
	int		nJs;
	double		Js[NJ_MAX];
	double		omegaJs[NJ_MAX];
	double		kappaJs[NJ_MAX];
	double		nuJs[NJ_MAX];
} KEP_PLANET;

typedef struct {
	double		a, e, i, peri, node, meanLon, epoch;
	double		eccRatio, cosI, sinI;
	double		omega, dPdT, dNdT;
	double		a2kappa2, dPNdT;
} KEP_ORBIT;

/*******************************************************************************
* External function prototypes
*******************************************************************************/

#ifdef __STDC__
#define PROTOTYPES
#endif

#ifdef VAXC
#define PROTOTYPES
#endif

#ifdef PROTOTYPES

void	Kep_SetPlanet( double radius, double gm, double *js, int nJs,
	        KEP_PLANET *planet );
void	Kep_SetError( double error );

double	Kep_Omega( KEP_PLANET *planet, double a );
double	Kep_dOmega(KEP_PLANET *planet, double a );
double	Kep_Kappa( KEP_PLANET *planet, double a );
double	Kep_dKappa(KEP_PLANET *planet, double a );
double	Kep_Nu(    KEP_PLANET *planet, double a );
double	Kep_dNu(   KEP_PLANET *planet, double a );
double	Kep_Combo( KEP_PLANET *planet, double a,
		int mOmega, int mKappa, int mNu );
double	Kep_dCombo(KEP_PLANET *planet, double a,
		int mOmega, int mKappa, int mNu );
void	Kep_5Freq( KEP_PLANET *planet, double a, double *omega, double *kappa,
		double *nu, double *apse, double *node );
double	Kep_SolveA(KEP_PLANET *planet, double value,
		int mOmega, int mKappa, int mNu );

void	Kep_SetOrbit( double a, double e, double i, double peri, double node,
		double meanLon, double epoch,
		KEP_PLANET *planet, KEP_ORBIT *orbit );
void	Kep_Precess( KEP_ORBIT *orbit, double time,
		double *peri, double *node, double *meanLon );
double	Kep_TrueAnom( double e, double meanAnom );
double	Kep_MeanAnom( double e, double trueAnom );
void	Kep_Locate( KEP_ORBIT *orbit, double time, double *location,
		double *velocity );

#else	/* The C compiler on Suns does not allow function prototypes */

void	Kep_SetPlanet();
void	Kep_SetError();
double	Kep_Omega(), Kep_dOmega();
double	Kep_Kappa(), Kep_dKappa();
double	Kep_Nu(),    Kep_dNu();
double	Kep_Combo(), Kep_dCombo();
void	Kep_5Freq();
double	Kep_SolveA();

void	Kep_SetOrbit();
void	Kep_Precess();
double	Kep_TrueAnom();
double	Kep_MeanAnom();
void	Kep_Locate();

#endif

/*******************************************************************************
* Internal function prototypes
*******************************************************************************/

#ifdef PROTOTYPES

double	XKep_Jseries(  double *coefftJs, int nJs, double ratio2 );
double	XKep_dJseries( double *coefftJs, int nJs, double ratio2 );
double	XKep_TrueAnom( double e, double eccRatio, double meanAnom,
		double *eccAnom );
double	XKep_MeanAnom( double e, double eccRatio, double trueAnom );

#else

double	XKep_Jseries();
double	XKep_dJseries();
double	XKep_TrueAnom();
double	XKep_MeanAnom();

#endif

/*******************************************************************************
* Functions handled as macros
*******************************************************************************/

#define	Kep_Apse( planet, a )	Kep_Combo( (planet), (a), 1, -1, 0 )
#define	Kep_Node( planet, a )	Kep_Combo( (planet), (a), 1, 0, -1 )

#define	Kep_dApse( planet, a )	Kep_dCombo( (planet), (a), 1, -1, 0 )
#define	Kep_dNode( planet, a )	Kep_dCombo( (planet), (a), 1, 0, -1 )

/******************************************************************************/
