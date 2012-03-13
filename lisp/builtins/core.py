from ..types import Procedure
from ..eval import EvalException

class QuoteProcedure(Procedure):
    def __init__(self):
        Procedure.__init__(self, 'quote')
    def call(self, scope, args):
        return args.car

def register(scope):
    scope.set('quote', QuoteProcedure())
