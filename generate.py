import sys
from collections import OrderedDict

from crossword import *
import operator


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        print("Before Node Consistency:",self.domains)
        for variable in self.domains:
            word_size=variable.length
            delete_word_set=set()
            for word in self.domains[variable]:
                if len(word)!=word_size:
                    delete_word_set.add(word)
            self.domains[variable]=self.domains[variable].difference(delete_word_set)
        print("After Node Consistency:", self.domains)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        modified=False

        print("Before revision:",self.domains[x])
        if self.crossword.overlaps[(x,y)] is None:
            return modified
        overlap_index =self.crossword.overlaps[(x,y)]
        print("overlap_index",overlap_index)
        print("y domains:",self.domains[y])
        delete_word_list=set()
        for x_word in self.domains[x]:
            has_mapping = False
            for y_word in self.domains[y]:
                if x_word[overlap_index[0]]==y_word[overlap_index[1]]:
                    has_mapping=True
                    break
            if not has_mapping:
                delete_word_list.add(x_word)
                modified= True
        self.domains[x]=self.domains[x].difference(delete_word_list)
        print("After revision:", self.domains[x])
        return modified

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is None:
            arcs=list()
            for variable in self.crossword.variables:
                print(self.crossword.neighbors(variable))
                for neighbour in self.crossword.neighbors(variable):
                    arcs.append((variable,neighbour))
        while len(arcs)!=0:
            arc=arcs.pop()
            if self.revise(arc[0],arc[1]):
                if len(self.domains[arc[0]])==0:
                    return False
                for neighbour in self.crossword.neighbors(arc[0]):
                    if neighbour!=arc[1]:
                        arcs.append((arc[0],neighbour))
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """

        return (len(assignment)==len(self.crossword.variables)) and all(variable in assignment for variable in self.crossword.variables)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        all_domain=list()

        for var in assignment:
            all_domain.append(assignment[var])
            neighbours=self.crossword.neighbors(var)
            if len(assignment[var])!=var.length:
                    return False
            for neighbour in neighbours:
                overlap_index=self.crossword.overlaps[(var,neighbour)]
                if neighbour in assignment:
                    if assignment[var][overlap_index[0]]!=assignment[neighbour][overlap_index[1]]:
                        return False

        if len(all_domain)!=len(set(all_domain)):
            return False

        return True





    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        domain_order=dict()

        for word in self.domains[var]:
            word_counter=0
            for neighbour in self.crossword.neighbors(var):
                if neighbour in assignment:
                    continue
                if word in self.domains[neighbour]:
                    word_counter+=1
            domain_order[word]=word_counter
        domain_order_list=list()
        for key, value in sorted(domain_order.items(), key=lambda x: x[1]):
            domain_order_list.append(key)
        return domain_order_list



    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned_var=self.domains.keys()-assignment.keys()
        min_domain_var=list()
        domain_size=float("inf")
        for var in unassigned_var:
            if len(self.domains[var])< domain_size:
                domain_size=len(self.domains[var])
                min_domain_var.clear()
                min_domain_var.append(var)
            elif len(self.domains[var])==domain_size:
                min_var=min_domain_var.pop()
                if len(self.crossword.neighbors(var))> len(self.crossword.neighbors(min_var)):
                    min_domain_var.append(var)
                else:
                    min_domain_var.append(min_var)

        return min_domain_var.pop()

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var= self.select_unassigned_variable(assignment)
        for word in self.order_domain_values(var,assignment):
            assignment_copy=assignment.copy()
            assignment_copy[var]=word
            back_up_domain = self.domains.copy()

            if self.consistent(assignment_copy):
                self.domains[var] = {word}
                inferences= self.inference_assignment(var,assignment)
                if inferences is not None:
                    assignment_copy.update(inferences)
                result = self.backtrack(assignment_copy)
                if result is None:
                    self.domains=back_up_domain
                else:
                    return result
        return None


    def inference_assignment(self, var, assignment):
        neighbours = self.crossword.neighbors(var)
        inference=dict()
        arcs=list()
        for neighbour in neighbours:
            if neighbour not in assignment:
                arcs.append((neighbour,var))
        if arcs:
            self.ac3(arcs)
            for arc in arcs:
                if len(self.domains[arc[0]])==1:
                    inference[arc[0]]=self.domains[arc[0]]
                elif len(self.domains[arc[0]])==0:
                    return None
        if inference:
            return inference
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    print("variables",crossword.variables)
    print("domains",crossword.words)
    creator = CrosswordCreator(crossword)
    print(creator.domains)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
