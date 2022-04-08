# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 18:21:17 2021

@author: weibel amine
"""

from pyomo.environ import *

model = ConcreteModel()

# Initialisation des variables
model.x1 = Var(within=NonNegativeReals)
model.x2 = Var(within=NonNegativeReals)
model.x3 = Var(within=NonNegativeReals)

# Contraintes
model.c1 = Constraint(expr=(model.x1 + model.x2 <= model.x3))
model.c2 = Constraint(expr=(model.x3 <= 1000))

# Fonction objective
function = model.x1 * (15-(2/100)*model.x1) + model.x2*(23-(1/100)*model.x2)-(2*model.x1+3.5*model.x2+3*model.x3)
model.objective = Objective(expr=function, sense=maximize)

# Optimisation
SolverFactory('mindtpy').solve(model, mip_solver='glpk', nlp_solver='ipopt', tee=True)


print('x1:'+str(model.x1.value))
print('x2:'+str(model.x2.value))
print('x3:'+str(model.x3.value))
print('Objective:'+str(model.objective.expr()))


# model.objective.display()
# model.display()
