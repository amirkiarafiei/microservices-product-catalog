"use client";

import { Github, Linkedin, GraduationCap, BookOpen, Globe } from "lucide-react";

export default function Footer() {
  const socialLinks = [
    {
      name: "Website",
      url: "https://www.amirkia.tech",
      icon: Globe,
    },
    {
      name: "GitHub",
      url: "https://github.com/amirkiarafiei",
      icon: Github,
    },
    {
      name: "Google Scholar",
      url: "https://scholar.google.com/citations?user=9geFFmwAAAAJ&hl=en",
      icon: GraduationCap,
    },
    {
      name: "LinkedIn",
      url: "https://www.linkedin.com/in/amirkiarafiei/",
      icon: Linkedin,
    },
    {
      name: "Medium",
      url: "https://medium.com/@amirkiarafiei",
      icon: BookOpen,
    },
  ];

  return (
    <footer className="bg-white border-t border-slate-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Left side - Copyright */}
          <div className="text-sm text-slate-600">
            © {new Date().getFullYear()} TMF Product Catalog. Built by{" "}
            <span className="font-medium text-slate-900">Amirkia Rafiei</span>
          </div>

          {/* Right side - Website & Social Links */}
          <div className="flex items-center gap-4">
            {/* Website text link */}
            <a
              href="https://www.amirkia.tech"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-600 hover:text-[#FF7900] transition-colors duration-200 font-medium"
            >
              www.amirkia.tech
            </a>
            
            {/* Separator */}
            <div className="hidden sm:block w-px h-5 bg-slate-300" />
            
            {/* Social Icons */}
            {socialLinks.slice(1).map((link) => (
              <a
                key={link.name}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-500 hover:text-[#FF7900] transition-colors duration-200"
                aria-label={link.name}
                title={link.name}
              >
                <link.icon className="w-5 h-5" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
