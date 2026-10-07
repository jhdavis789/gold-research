/* Exact cash/gradient recursion. No fast-math, prices or fitted parameters here. */
void cash_path(int n,int k,double initial,const double *initial_grad,
 const double *growth,const double *years,const double *short_factor,
 double short_position,const double *short_grad,
 const double *flow,const double *flow_grad,double borrow,
 double *cash,double *grad) {
 cash[0]=initial;
 for(int z=0;z<k;z++) grad[z]=initial_grad[z];
 for(int j=1;j<n;j++) {
  double g=growth[j];
  if(cash[j-1]<0.) g*=1.+borrow*years[j];
  cash[j]=cash[j-1]*g+short_position*short_factor[j]+flow[j];
  for(int z=0;z<k;z++)
   grad[j*k+z]=grad[(j-1)*k+z]*g+short_grad[z]*short_factor[j]+flow_grad[j*k+z];
 }
}
