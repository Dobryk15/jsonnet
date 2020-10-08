import unittest
import infer
import hm_algo


class TestTypeInference(unittest.TestCase):

    def test_number(self):
        self.assertEqual(infer.run("{x: 1}"), "{x: number}")

    def test_boolean(self):
        self.assertEqual(infer.run("{x: true}"), "{x: boolean}")

    def test_string(self):
        self.assertEqual(infer.run("{x: 'a'}"), "{x: string}")
    
    def test_empty_object(self):
        example = """(
            {}
        )"""
        inferred_type = "{}"
        self.assertEqual(infer.run(example), inferred_type)

    def test_inheritance(self):
        example = """(
            {
                local person = {
                    name: '',
                },
                student: person { 
                    name: 'Ali', 
                    age: 19,
                    best_friend: person {
                        age: 18,
                        has_friend: true
                    }  
                },
            }
        )"""
        inferred_type = "{student: {name: string, age: number, best_friend: {age: number, has_friend: boolean, name: string}}}"
        self.assertEqual(infer.run(example), inferred_type)

    def test_type_mismatch_error(self):
        example = """(
            {
                local person = {
                    name: 0,
                },
                student: person { 
                    name: 'Ali', 
                },
            }
        )"""
        error_msg = "Type mismatch: string != number, lines 6-8, field 'name'"
        self.assertEqual(infer.run(example), error_msg)

    def test_mutual_rec(self):
        example = """(
            {
                euro: self.dol,
                dol: self.euro,
            }
        )"""
        inferred_type = "{euro: a, dol: a}"
        self.assertEqual(infer.run(example), inferred_type)

    def test_local_field_rec(self):
        example = """(
            {
                local x = y, 
                local y = self.z, 
                z: 2,
                t: x 
            }
        )"""
        inferred_type = "{z: number, t: number}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def test_binary_plus(self):
        example = """(
            {
                x: 1,
                y: 2,
                z: self.x + self.y
            }
        )"""
        inferred_type = "{x: number, y: number, z: number}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def test_binary_plus_type_error(self):
        example = """(
            {
                x: 1,
                y: true,
                z: self.x + self.y
            }
        )"""
        error_msg = "Type mismatch: boolean != number, line 5"
        self.assertEqual(infer.run(example), error_msg)
    
    def test_using_local_obj_with_inheritance(self):
        example = """(
            {
                local a = self.b {
                    e: true
                },
                b: {
                    d: 1,
                },
                c: a
            }
        )"""
        inferred_type = "{b: {d: number}, c: {e: boolean, d: number}}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def test_inherit_param_inside_func(self):
        example = """(
            { 
                local f(base) = { 
                    x: base { 
                        a: 3 
                    }, 
                    y: base { 
                        a: "str" 
                    } 
                }, 
                res: f({ a: null }) 
            }
        )"""
        error_msg = "Type mismatch: string != number"
        self.assertEqual(infer.run(example), error_msg)
    
    def test_inherit_base_twice(self):
        example = """(
            { 
                local base = { 
                    a: null 
                }, 
                x: base { 
                    a: 3 
                }, 
                y: base { 
                    a: "str" 
                } 
            }
        )"""
        inferred_type = "{x: {a: number}, y: {a: string}}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def test_inheritance_failure(self):
        example = """(
            { 
                local currency = { 
                    euro: self.dollar, 
                    dollar: self.euro 
                }, 
                x: currency { 
                    euro: 1, 
                    dollar: 'smth' 
                } 
            }
        )"""
        error_msg = "Type mismatch: string != number"
        self.assertEqual(infer.run(example), error_msg)

    def test_inheritance2(self):
        example = """(
            { 
                local base = { 
                    local b = self.a {
                        z: 3,
                    },
                    a: {
                        z: null    
                    },
                }, 
                x: base {k: 1}, 
                y: base {s: "str" } 
            }
        )"""
        inferred_type = "{x: {k: number, a: {z: number}}, y: {s: string, a: {z: number}}}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def test_unrecognized_base_field(self):
        example = """(
            { 
                local l = {
                    x: 3,
                    y: 4
                },
                z: l {
                    t: self.y
                }
            }
        )"""
        inferred_type = "{z: {t: number, x: number, y: number}}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def test_unrecognized_base__func_field(self):
        example = """(
            { 
                local f(base) = { 
                    a: base
                }, 
                res: f(1) {
                    b: self.a
                } 
            }
        )"""
        inferred_type = "{z: {t: number, x: number, y: number}}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def test_unrecognized_child_field(self):
        example = """(
            { 
                local base = { 
                    z: self.k
                }, 
                x: base {k: 1} 
            }
        )"""
        inferred_type = "{x: {k: number, z: number}}"
        self.assertEqual(infer.run(example), inferred_type)
    
    def inheritance_that_violates_type_copy(self):
        example = """(
            {
                x: self.y {
                    z: true
                },
                y: {
                    t: 1,
                },
            }

        )"""
        inferred_type = "{x: {z: boolean, t: number} y: {t: number}}"
        self.assertEqual(infer.run(example), inferred_type)

    def test_simple_case_to_fix_inheritance(self):
        example = """(
            {
                local a = self.b {
                    e: true
                },
                b: {
                    d: 1,
                }
            }
        )"""
        inferred_type = "{b: {d: number}}"
        self.assertEqual(infer.run(example), inferred_type)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestTypeInference('test_number'))
    suite.addTest(TestTypeInference('test_boolean'))
    suite.addTest(TestTypeInference('test_string'))
    suite.addTest(TestTypeInference('test_empty_object'))
    suite.addTest(TestTypeInference('test_inheritance'))
    suite.addTest(TestTypeInference('test_mutual_rec'))
    suite.addTest(TestTypeInference('test_type_mismatch_error'))
    suite.addTest(TestTypeInference('test_local_field_rec'))
    suite.addTest(TestTypeInference('test_binary_plus'))
    suite.addTest(TestTypeInference('test_binary_plus_type_error'))
    suite.addTest(TestTypeInference('test_using_local_obj_with_inheritance'))
    suite.addTest(TestTypeInference('test_inherit_param_inside_func'))
    suite.addTest(TestTypeInference('test_inherit_base_twice'))
    suite.addTest(TestTypeInference('test_inheritance_failure'))
    suite.addTest(TestTypeInference('test_inheritance2'))
    suite.addTest(TestTypeInference('test_unrecognized_base_field'))
    suite.addTest(TestTypeInference('test_unrecognized_base__func_field'))
    suite.addTest(TestTypeInference('test_unrecognized_child_field'))
    suite.addTest(TestTypeInference('inheritance_that_violates_type_copy'))
    suite.addTest(TestTypeInference('test_simple_case_to_fix_inheritance'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
