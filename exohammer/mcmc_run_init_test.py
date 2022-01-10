#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  3 11:04:17 2021

@author: nickjuliano
"""
from exohammer.utilities import *

class mcmc_run:
    import emcee
    import os
        
    def __init__(self, planetary_system, data, lnprob=None):
        import os
        import datetime
        import emcee
        from exohammer.system_init_test import system
        date        = str(datetime.datetime.now().date())+'_'+str(datetime.datetime.now().time())[:-7]
        output_path = str(os.path.abspath(os.getcwd()) + "/Output/")
        os.mkdir(output_path + 'run_' + date)
        output_path=output_path+'run_'+ date+"/"
        self.output_path = output_path
        self.date        = date
        self.EnsembleSampler = emcee.EnsembleSampler
        self.system = system(planetary_system, data, lnprob)

    def explore(self, iterations, thin=1, moves = [(emcee.moves.DEMove(), 0.8), (emcee.moves.DESnookerMove(), 0.2)], verbose=True, tune=True):
        import numpy as np
        walk=self.system.ndim*3
        self.nwalkers       = int(walk) if ((int(walk) % 2) == 0) else int(walk) + 1
        self.nburnin        = int(0.1*iterations)
        self.thin           = thin
        self.niter          = int(iterations-self.nburnin)
        self.moves          = moves
        self.discard        = 0
        
        lnprob              = self.system.lnprob
        ndim                = self.system.ndim
        nwalkers            = self.nwalkers
        nburnin             = self.nburnin
        thin             = self.thin
        
        p0=self.system.initial_state(self.nwalkers)
        # Initialize the sampler
        sampler = self.EnsembleSampler(self.nwalkers, ndim, lnprob, args=[self.system], moves=moves)#, backend=backend)
        
        print("Running burn-in... " + str(self.nburnin)+ " steps")
        
        p0, _, _ = sampler.run_mcmc(p0, nburnin, progress=verbose)
        sampler.reset()

        print("Running production..." + str(self.niter)+ " steps")
        pos, prob, state = sampler.run_mcmc(p0, self.niter, thin=thin, progress=verbose, tune=tune)
        
        self.sampler   = sampler 
        self.pos       = pos 
        self.prob      = prob 
        self.state     = state 
        
        def sampler_to_theta_max(self):
            import numpy as np
            sampler=self.sampler
            samples = sampler.get_chain(flat=True, thin=self.thin)
            self.samples = samples
            self.theta_max = samples[np.argmax(sampler.get_log_prob(flat=True, thin=self.thin))]
        sampler_to_theta_max(self) 
    
        
    def plot_corner(self):
        import matplotlib.pyplot as plt
        import corner
        filename= self.output_path + "corner_" + self.date + '.png'
        samples = self.samples
        figure = corner.corner(samples, labels=self.system.variable_labels)
        figure.savefig(filename)
        plt.show()



    def plot_chains(self, discard=None):
        import matplotlib.pyplot as plt
        filename= self.output_path + "Chains_" + self.date +'.png'
        #samples = self.samples
        if discard == None:
            discard=self.discard
        samples = self.sampler.get_chain(discard=discard)
        fig, axes = plt.subplots(len(self.system.variable_labels), figsize=(20, 30), sharex=True)
        fig.suptitle('chains', fontsize=30)
        for i in range(len(self.system.variable_labels)):
            ax = axes[i]
            ax.plot(samples[:, :, i ], "k", alpha=0.3)
            ax.set_xlim(0, len(samples))
            ax.set_ylabel(self.system.variable_labels[i])
            ax.yaxis.set_label_coords(-0.1, 0.5)
        plt.savefig(filename)
        plt.show()
        
        
        
    def summarize(self):
        space = """

            """
        summary="""
            This run sampled %i walkers with %i iterations with a burn-in of %i.  

            The chain was thinned by %i

            The resultant orbital elements are below:

            """%(self.nwalkers, self.niter, self.discard, self.thin)
        run_description = open(self.output_path + "/run_description_"+self.date+".txt", "w+")
        run_description.write(summary)
        run_description.write(space)
        run_description.write(str(self.system.variable_labels))
        run_description.write(space)
        #theta=self.theta_max
        run_description.write(str(self.theta_max))
        print(summary)
        print(self.system.variable_labels)
        print(self.theta_max)
        
        
        
    def autocorr(self):
        filename = self.output_path + "autocor_" + self.date + '.txt'
        #autocor  = open(self.output_path + "/autocor_"+self.date+".txt", "w+")
        try:
            tau        = self.sampler.get_autocorr_time(discard=self.discard)
        except Exception as e:
            print(str(e))
            tau = e
        with open(filename, 'w') as f:
            f.write(str(tau))
        return tau
    
    def plot_rvs(self):
        import matplotlib
        import matplotlib.pyplot as plt
        from exohammer.utilities import model
        from exohammer.analyze import plot_rvs

        orbital_elements = self.system.orbital_elements
        tmin             = self.system.tmin
        tmax             = self.system.tmax
        nplanets         = self.system.nplanets
        
        output_path      = self.output_path
        date             = self.date
        theta=self.theta_max
        rvbjd            = self.system.rvbjd
        rvmnvel          = self.system.rvmnvel 
        rverrvel         = self.system.rverrvel 
        __, __, rv_model = model(self.theta_max, self.system)
        filename= self.output_path + "rvs_" + self.date + '.png'
        plot_rvs(self.system.rvbjd, self.system.rvmnvel, self.system.rverrvel, rv_model, filename)
    
    def plot_ttvs(self):
        import matplotlib
        import matplotlib.pyplot as plt
        from exohammer.utilities import model
        from exohammer.analyze import plot_ttvs

        orbital_elements = self.system.orbital_elements
        tmin             = self.system.tmin
        tmax             = self.system.tmax
        nplanets         = self.system.nplanets_fit
        
        output_path      = self.output_path
        date             = self.date
        theta=self.theta_max
        measured            = self.system.measured
        epoch          = self.system.epoch 
        error         = self.system.error 
        model, model_epoch, __ = model(self.theta_max, self.system)
        filename= self.output_path + "TTVs_" + self.date + '.png'
        plot_ttvs(nplanets, measured, epoch, error, model, model_epoch, filename)
    
    def autocorr(self):
        filename = self.output_path + "autocor_" + self.date + '.txt'
        #autocor  = open(self.output_path + "/autocor_"+self.date+".txt", "w+")
        try:
            tau        = self.sampler.get_autocorr_time(discard=self.discard)
        except Exception as e:
            print(str(e))
            tau = e
        with open(filename, 'w') as f:
            f.write(str(tau))
        return tau
    
    def summarize(self):
        space = """

            """
        summary="""
            This run sampled %i walkers with %i iterations with a burn-in of %i.  

            The chain was thinned by %i

            The resultant orbital elements are below:

            """%(self.nwalkers, self.niter, self.discard, self.thin)
        run_description = open(self.output_path + "/run_description_"+self.date+".txt", "w+")
        run_description.write(summary)
        run_description.write(space)
        run_description.write(str(self.system.variable_labels))
        run_description.write(space)
        #theta=self.theta_max
        run_description.write(str(self.theta_max))
        print(summary)
        print(self.system.variable_labels)
        print(self.theta_max)
        
    def save_misc_txt(self, filename, info, more_info=None):
        filename = self.output_path + filename+"_" + self.date + '.txt'
        with open(filename, 'w') as f:
            f.write(str(info))
            if more_info!=None:
                f.write(more_info)
        return