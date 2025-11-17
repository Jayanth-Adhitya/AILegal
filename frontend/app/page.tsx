"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import {
  FileText,
  Shield,
  Zap,
  Users,
  CheckCircle2,
  ArrowRight,
  Scale,
  Mail,
  MapPin,
  Phone,
} from "lucide-react";
import {
  heroText,
  heroCTA,
  staggerContainer,
  featureCardVariants,
} from "@/lib/animations";
import { GradientText, BlurText } from "@/components/ui/animated-text";
import { SpotlightCard, MagneticButton } from "@/components/ui/animated-card";
import { DotGrid } from "@/components/ui/dot-grid";
import { ShuffleText } from "@/components/ui/shuffle-text";

export default function LandingPage() {
  const router = useRouter();
  const { user } = useAuth();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (user) {
      router.push("/dashboard");
    }
  }, [user, router]);

  // Don't render landing page for authenticated users
  if (user) {
    return null;
  }

  const features = [
    {
      icon: FileText,
      title: "Smart Contract Analysis",
      description:
        "AI-powered clause-by-clause analysis against your company policies with risk assessment.",
    },
    {
      icon: Shield,
      title: "Policy Compliance",
      description:
        "Automatically check contracts against UAE legal requirements and internal policies.",
    },
    {
      icon: Zap,
      title: "Instant Redlines",
      description:
        "Generate track changes and alternative clause suggestions in seconds.",
    },
    {
      icon: Users,
      title: "AI Negotiation",
      description:
        "Multi-agent negotiation where AI agents represent different parties.",
    },
  ];

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F9F5F1' }}>
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <DotGrid
          dotSize={3}
          gap={28}
          baseColor="#d4a60a"
          activeColor="#000000"
          proximity={150}
          className="opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-yellow-300/20 to-transparent" />

        <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
            {/* Left side - Text content */}
            <motion.div
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
              className="text-left"
            >
              {/* Brand Icon */}
              <motion.div
                variants={heroText}
                className="mb-8 flex h-20 w-20 items-center justify-center rounded-2xl glass-card"
              >
                <Scale className="h-10 w-10 text-yellow-600" />
              </motion.div>

              {/* Main Heading */}
              <motion.h1
                variants={heroText}
                className="font-display font-bold tracking-tight text-gray-900"
              >
                <GradientText className="block text-5xl xs:text-6xl sm:text-7xl lg:text-8xl">
                  <ShuffleText text="Cirilla" duration={3000} />
                </GradientText>
                <span className="block text-2xl xs:text-3xl sm:text-4xl lg:text-5xl mt-2 text-gray-700">
                  AI-Powered Legal Assistant
                </span>
              </motion.h1>

              {/* Description */}
              <motion.p
                variants={heroText}
                className="mt-6 text-base leading-7 text-gray-600 sm:text-lg sm:leading-8 max-w-xl"
              >
                Automate contract review, ensure policy compliance, and accelerate
                negotiations with intelligent AI analysis tailored for{" "}
                <span className="font-semibold text-yellow-600">UAE legal requirements</span>.
              </motion.p>

              {/* CTA Buttons */}
              <motion.div
                variants={heroCTA}
                className="mt-8 flex flex-col gap-4 sm:mt-10 sm:flex-row sm:gap-x-6"
              >
                <MagneticButton>
                  <Button asChild size="lg" className="w-full text-base sm:w-auto">
                    <Link href="/register">
                      Get Started
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Link>
                  </Button>
                </MagneticButton>
                <MagneticButton>
                  <Button asChild variant="outline" size="lg" className="w-full text-base sm:w-auto">
                    <Link href="/login">Sign In</Link>
                  </Button>
                </MagneticButton>
              </motion.div>
            </motion.div>

            {/* Right side - Demo GIF placeholder */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="relative hidden lg:block"
            >
              <div className="glass-card rounded-2xl p-4 shadow-dual-xl">
                <div className="aspect-video w-full rounded-lg bg-yellow-100/50 flex items-center justify-center">
                  <span className="text-yellow-600 font-medium">Demo GIF Here</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="mx-auto max-w-7xl px-6 py-24 lg:px-8">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
          className="text-center"
        >
          <motion.h2
            variants={heroText}
            className="font-display text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl"
          >
            Everything you need for contract management
          </motion.h2>
          <motion.p
            variants={heroText}
            className="mx-auto mt-4 max-w-2xl text-lg text-gray-600"
          >
            Streamline your legal workflow with AI-driven insights and automation.
          </motion.p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="mt-12 grid gap-6 sm:mt-16 sm:grid-cols-2 sm:gap-8 lg:grid-cols-4"
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              custom={index}
              variants={featureCardVariants}
              whileHover={{ y: -8, transition: { duration: 0.2 } }}
            >
              <SpotlightCard className="h-full p-6">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-yellow-200/50">
                  <feature.icon className="h-6 w-6 text-yellow-700" />
                </div>
                <h3 className="text-base font-semibold text-gray-900 sm:text-lg">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm text-gray-600">{feature.description}</p>
              </SpotlightCard>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Benefits Section */}
      <div className="bg-yellow-500/10 py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={staggerContainer}
            className="glass-panel rounded-2xl p-6 sm:p-8 lg:p-12"
          >
            <div className="grid gap-8 lg:grid-cols-2 lg:gap-16">
              <div>
                <motion.h3
                  variants={heroText}
                  className="font-display text-xl font-bold text-gray-900 sm:text-2xl lg:text-3xl"
                >
                  Why choose our platform?
                </motion.h3>
                <motion.p
                  variants={heroText}
                  className="mt-4 text-sm text-gray-700 sm:text-base"
                >
                  Built specifically for legal professionals in the UAE, our
                  platform combines cutting-edge AI with deep understanding of
                  local regulations.
                </motion.p>
              </div>

              <motion.ul
                variants={staggerContainer}
                className="space-y-4"
              >
                {[
                  "UAE PDPL compliant data handling",
                  "Bilingual support (English/Arabic)",
                  "Real-time collaboration features",
                  "Audit trail for all AI decisions",
                  "Human-in-the-loop approval workflow",
                  "Voice-enabled interactions",
                ].map((benefit, index) => (
                  <motion.li
                    key={benefit}
                    custom={index}
                    variants={featureCardVariants}
                    className="flex items-start gap-3"
                  >
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-yellow-600" />
                    <span className="text-gray-700">{benefit}</span>
                  </motion.li>
                ))}
              </motion.ul>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Contact Us Section */}
      <div className="mx-auto max-w-7xl px-6 py-24 lg:px-8">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.h2
            variants={heroText}
            className="font-display text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl text-center mb-12"
          >
            Get in Touch
          </motion.h2>
          <div className="grid gap-8 md:grid-cols-3">
            <motion.div
              variants={featureCardVariants}
              className="glass-card rounded-xl p-6 text-center"
            >
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-yellow-200/50">
                <Mail className="h-6 w-6 text-yellow-700" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Email Us</h3>
              <a
                href="mailto:reach@cirilla.ai"
                className="text-yellow-600 hover:text-yellow-700 transition-colors"
              >
                reach@cirilla.ai
              </a>
            </motion.div>
            <motion.div
              variants={featureCardVariants}
              className="glass-card rounded-xl p-6 text-center"
            >
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-yellow-200/50">
                <Phone className="h-6 w-6 text-yellow-700" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Call Us</h3>
              <a
                href="tel:+97142345678"
                className="text-yellow-600 hover:text-yellow-700 transition-colors"
              >
                +971 4 234 5678
              </a>
            </motion.div>
            <motion.div
              variants={featureCardVariants}
              className="glass-card rounded-xl p-6 text-center"
            >
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-yellow-200/50">
                <MapPin className="h-6 w-6 text-yellow-700" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Visit Us</h3>
              <p className="text-gray-600">
                Dubai Internet City<br />
                Dubai, UAE
              </p>
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* Final CTA */}
      <div className="mx-auto max-w-7xl px-6 py-24 lg:px-8">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={staggerContainer}
          className="glass-intense rounded-2xl p-12 text-center"
        >
          <motion.h2
            variants={heroText}
            className="font-display text-3xl font-bold text-gray-900"
          >
            Ready to transform your legal workflow?
          </motion.h2>
          <motion.p
            variants={heroText}
            className="mx-auto mt-4 max-w-xl text-gray-700"
          >
            Join forward-thinking legal teams who are already saving hours on
            contract review.
          </motion.p>
          <motion.div variants={heroCTA} className="mt-8">
            <Button asChild size="lg" className="text-base">
              <Link href="/register">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </motion.div>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="border-t border-yellow-300/30 bg-yellow-100/50 py-12">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="grid gap-8 md:grid-cols-3">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Scale className="h-6 w-6 text-yellow-600" />
                <span className="font-display font-bold text-xl text-gray-900">
                  Cirilla
                </span>
              </div>
              <p className="text-sm text-gray-600">
                AI-Powered Legal Assistant for modern legal teams.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Quick Links</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="/login" className="text-gray-600 hover:text-yellow-600 transition-colors">
                    Sign In
                  </Link>
                </li>
                <li>
                  <Link href="/register" className="text-gray-600 hover:text-yellow-600 transition-colors">
                    Get Started
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Contact</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>reach@cirilla.ai</li>
                <li>+971 4 234 5678</li>
                <li>Dubai, UAE</li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-yellow-300/30 text-center">
            <p className="text-sm text-gray-600">
              &copy; {new Date().getFullYear()} Cirilla. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
