import numpy as np
from src.config import CentreFindConfig

class PMT_circle_fitting():

        self.R_p0 = cfg.PMT_bulb_radius
        self.p0 = np.array([p0_center[0],p0_center[1],self.R_p0])
        self.limits = np.array([p0_center_limits[0],p0_center_limits[1],5.])
        self.label = ["x0", "y0", "R"]
        self.x_data = np.array([])
        self.y_data = np.array([])
        self.parameter_best_fit = [0.,0.,0.]
        self.parameter_sigma = [0.,0.,0.]
        self._ndim = 3
        self.mcmc_status = False
        self.profile_length = 10.
        self.R_photocathode_error = 5.
        self.R_gaussian_spread = .5

    def __log_posterior(self,theta,x,y):
        lp = self.__log_prior(theta)
        if not np.isfinite(lp):
            return -np.inf
        return lp + self.__log_likelihood(theta,x,y)

    def __log_prior(self,theta):
        for parameter, lim in zip(theta, self.limits):
            if not (parameter-lim < parameter < parameter+lim):
                return -np.inf
        return 0.0

    def __log_likelihood(self,theta,x,y):
        xc, yc, R = theta
        model = np.sqrt((x-xc)**2.+(y-yc)**2.)-R
        return -0.5 * np.sum((model) ** 2 / self.R_gaussian_spread** 2) 
    
    def minimize(self):
        """
        Finds the best llh results for the centre and radius of PMT. It also calls estimate_uncertainty(False) for estimating uncertainties.
        Returns
        -------
        best_fit : float array
                Best llh fit for parameters [x0, y0, R]
        sigma : float array
                Uncertainties of best_fit [dx, dy, dR]
        status : bool
                Minimizer and mcmc status
        """
        if self.x_data.size>0:
            from scipy.optimize import minimize
            nll = lambda *args: -self.__log_posterior(*args)
            soln = minimize(nll, self.p0, args=(self.x_data, self.y_data))
            if soln.success:
                print("Minimum found at:")
                for i in range(self._ndim): 
                    print("\t - "+self.label[i]+"=",soln.x[i])
                self.parameter_best_fit = soln.x
#                print("I will estimate the uncertainties now...")
#                self.estimate_uncertainty()
#                print("Results:")
#                for i in range(self._ndim): 
#                    print("\t - d"+self.label[i]+" = ",self.parameter_sigma[i])
            else:
                print("No minimum found. Check starting values (.p0 object) and errors (.p0_error object).")
            return(self.parameter_best_fit, self.parameter_sigma, soln.success*self.mcmc_status)
        else:
            print("No data to minimize.")
            return(self.parameter_best_fit, self.parameter_sigma, False)
#    def estimate_uncertainty(self, with_plots = False):
#        """
#        Estimates uncertainties by producing PDF running a Markov chain Montecarlo around minimum.
#        Parameters
#        -------
#        with_plots : bool, default False
#                    runs self.plot_mcmc() if True
#        
#        """
#        import emcee  
#        nwalkers = 20  
#        xerror, yerror, Rerror = self.p0_error
#
#        p0 = np.array([np.random.uniform(low=-xerror, high=xerror, size=(nwalkers))+ self.parameter_best_fit[0],
#                     np.random.uniform(low=-yerror, high=yerror, size=(nwalkers))+ self.parameter_best_fit[1],
#                     np.random.uniform(low=-Rerror, high=Rerror, size=(nwalkers))+ self.parameter_best_fit[2]])
#        sampler = emcee.EnsembleSampler(nwalkers, self._ndim, self.__log_posterior, args=(self.x_data,self.y_data))
#        state = sampler.run_mcmc(p0.T, 10000) 
#        self.samples = sampler.get_chain()
#        self.flat_samples = sampler.get_chain(discard=1000, thin=15, flat=True)
#        self.mcmc_status = True
#        for i in range(self._ndim):
#            mcmc = np.percentile(self.flat_samples[:, i], [16, 50, 84])
#            q = np.diff(mcmc)
#            self.parameter_sigma[i] = 0.5*(q[0]+q[1])
#        if with_plots:
#            self.plot_mcmc()
#    def plot_mcmc(self):
#        """
#        Plots the MCMC steps and corner plot of PDF if the minimization and MCMC were successful.
#        
#        """
#        if self.mcmc_status:
#            import matplotlib.pyplot as plt
#            import corner
#            fig, axes = plt.subplots(self._ndim, figsize=(10, 7), sharex=True)
#            for i in range(self._ndim):
#                ax = axes[i]
#                ax.plot(self.samples[:, :, i], "k", alpha=0.3)
#                ax.set_xlim(0, len(self.samples))
#                ax.set_ylabel(self.label[i])
#                ax.yaxis.set_label_coords(-0.1, 0.5)
#            fig = corner.corner(
#                self.flat_samples, labels=self.label, quantiles=[0.16, 0.5, 0.84],show_titles=True, smooth=1, 
#            );
#        else:
#            print("For plotting the Markov Chain Montecarlo results, you first have to minimize!")
